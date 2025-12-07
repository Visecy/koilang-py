//! Python bindings for KoiLang parser module
//!
//! This module provides Python bindings for the koicore parser functionality,
//! allowing Python code to parse KoiLang files and handle parsing operations.

use pyo3::PyClassGuard;
use pyo3::exceptions::PyValueError;
use pyo3::{prelude::*, types::PyString};
use std::sync::{Arc, Mutex};
use std::io;

use crate::command::PyCommand;
use crate::error::raise_parser_err;
use crate::traceback::add_traceback;
use koicore::parser::{ErrorInfo, FileInputSource, Parser, ParserConfig, TextInputSource};

#[derive(Debug, Default, Clone, FromPyObject)]
pub struct PyParserConfig {
    pub command_threshold: Option<usize>,
    pub skip_annotations: bool,
    pub convert_number_command: bool,
    pub skip_add_traceback: bool,
}

impl From<PyParserConfig> for ParserConfig {
    fn from(config: PyParserConfig) -> Self {
        Self {
            command_threshold: config.command_threshold .unwrap_or(1),
            skip_annotations: config.skip_annotations,
            convert_number_command: config.convert_number_command,
        }
    }
}

/// Rust wrapper for Python file-like objects implementing TextInputSource
pub struct PyFileSource {
    file: Py<PyAny>,
    source_name: String,
}

impl PyFileSource {
    /// Create a new PyFileSource from a Python file-like object
    pub fn new(file: Bound<'_, PyAny>) -> PyResult<Self> {
        file.getattr("readline")?;

        let source_name = match file.getattr("name") {
            Ok(name_attr) => name_attr
                .extract::<String>()
                .unwrap_or_else(|_| "<string>".into()),
            Err(_) => "<string>".into(),
        };

        Ok(Self {
            file: file.unbind(),
            source_name,
        })
    }
}

impl TextInputSource for PyFileSource {
    fn next_line(&mut self) -> io::Result<Option<String>> {
        Python::attach(|py| {
            // 调用 readline 并处理异常
            let result = self.file.call_method0(py, "readline");

            match result {
                Ok(line) => {
                    let line = line.bind(py);
                    let line_str: &Bound<'_, PyString> = line.cast().map_err(|_| {
                        io::Error::new(
                            io::ErrorKind::InvalidData,
                            "readline() returned non-string value",
                        )
                    })?;

                    let is_empty = line_str.is_empty();
                    match is_empty {
                        Ok(true) => return Ok(None),
                        Err(pyerr) => {
                            return Err(io::Error::new(
                                io::ErrorKind::Other,
                                pyerr,
                            ));
                        }
                        _ => {}
                    };

                    let rust_str = line_str
                        .to_str()
                        .map_err(|e| {
                            io::Error::new(
                                io::ErrorKind::InvalidData,
                                format!("Invalid UTF-8 in input: {}", e),
                            )
                        })?
                        .to_string();

                    Ok(Some(rust_str))
                }
                Err(pyerr) => {
                    // 返回通用 IO 错误（会被上层忽略）
                    Err(io::Error::new(
                        io::ErrorKind::Other,
                        pyerr,
                    ))
                }
            }
        })
    }

    fn source_name(&self) -> String {
        self.source_name.clone()
    }
}

/// Python binding for the KoiLang parser
#[pyclass(name = "Parser",)]
pub struct PyParser {
    config: PyParserConfig,
    inner: Parser<Arc<Mutex<dyn TextInputSource + Send>>>,
}

#[pymethods]
impl PyParser {
    /// Create a new parser from string input
    ///
    /// Args:
    ///     text: The KoiLang text to parse
    ///     config: Configuration dict with optional keys:
    ///         - command_threshold: int (default: 1)
    ///         - skip_annotations: bool (default: false)
    ///         - convert_number_command: bool (default: true)
    #[new]
    #[pyo3(signature = (path_or_file, /, config = None))]
    pub fn new(path_or_file: Bound<'_, PyAny>, config: Option<PyParserConfig>) -> PyResult<Self> {
        // Parse configuration if provided
        let config = config.unwrap_or_default();

        // Check if input is a string (for string-based parsing)
        if let Ok(text) = path_or_file.extract::<String>() {
            let string_source = FileInputSource::new(text)?;
            let arc_input: Arc<Mutex<dyn TextInputSource + Send>> = Arc::new(Mutex::new(string_source));
            let parser = Parser::new(arc_input.clone(), config.clone().into());
            return Ok(Self {
                config: config,
                inner: parser,
            });
        }

        // Check if input is a path-like object (has __fspath__ or is str path)
        if let Ok(path_obj) = path_or_file.getattr("__fspath__") {
            let path_str: String = path_obj.call0()?.extract()?;
            match FileInputSource::new(path_str) {
                Ok(file_source) => {
                    let arc_input: Arc<Mutex<dyn TextInputSource + Send>> = Arc::new(Mutex::new(file_source));
                    let parser = Parser::new(arc_input.clone(), config.clone().into());
                    return Ok(Self {
                        config: config,
                        inner: parser,
                    });
                }
                Err(e) => {
                    return Err(PyValueError::new_err(format!(
                        "Failed to create file source: {}",
                        e
                    )));
                }
            }
        }
        let py_file_source = PyFileSource::new(path_or_file)?;
        let arc_input: Arc<Mutex<dyn TextInputSource + Send>> = Arc::new(Mutex::new(py_file_source));
        let parser = Parser::new(arc_input.clone(), config.clone().into());
        Ok(Self {
            config: config,
            inner: parser,
        })
    }

    /// Get the next command from the input
    ///
    /// Returns:
    ///     PyCommand object if a command is found
    ///     None if end of input is reached
    ///     
    /// Raises:
    ///     ParseError if parsing fails
    pub fn next_command(&mut self, py: Python<'_>) -> PyResult<Option<PyCommand>> {
        match self.inner.next_command() {
            Ok(Some(command)) => Ok(Some(PyCommand::from(command))),
            Ok(None) => Ok(None),
            Err(parse_error) => {
                if let ErrorInfo::IoError { error } = parse_error.error_info {
                    return Err(error.into());
                }
                
                let err_source = parse_error.source.clone();
                let mut exc = raise_parser_err(parse_error);
                if let Some(source) = err_source {
                    if !self.config.skip_add_traceback {
                        exc = add_traceback(exc, py, &source.filename, "<kola>", source.lineno);
                    }
                }
                Err(exc)
            },
        }
    }

    /// Get an iterator over the parser commands
    ///
    /// Returns:
    ///     PyParser object itself, which can be iterated over
    pub fn __iter__(slf: PyClassGuard<'_, Self>) -> PyClassGuard<'_, Self> {
        slf
    }

    /// Get the next command from the parser
    ///
    /// Returns:
    ///     PyCommand object if a command is found
    ///     None if end of input is reached
    ///     
    /// Raises:
    ///     ParseError if parsing fails
    pub fn __next__(&mut self, py: Python<'_>) -> PyResult<PyCommand> {
        match self.next_command(py)? {
            Some(command) => Ok(command),
            None => Err(PyErr::new::<pyo3::exceptions::PyStopIteration, ()>(())),
        }
    }

    /// Process all commands using a callback function
    ///
    /// Args:
    ///     callback: Python function that takes a PyCommand and returns bool
    ///               Return True to continue, False to stop processing
    ///
    /// Returns:
    ///     bool indicating if processing reached end of input
    ///
    /// Raises:
    ///     ParseError if parsing fails
    ///     Exception if callback raises an exception
    pub fn process_with(&mut self, py: Python<'_>, callback: Bound<'_, PyAny>) -> PyResult<bool> {
        let parser = &mut self.inner;

        // Check if callback is callable
        if !callback.is_callable() {
            return Err(PyValueError::new_err("Callback must be callable"));
        }

        loop {
            match parser.next_command() {
                Ok(Some(command)) => {
                    let py_command = PyCommand::from(command);

                    // Call the Python callback with the command
                    let result = callback.call1((py_command,))?;

                    // Check if callback returned False (to stop processing)
                    let should_continue: bool = result.extract()?;
                    if !should_continue {
                        return Ok(false); // Processing stopped by callback
                    }
                }
                Ok(None) => {
                    return Ok(true); // Reached end of input
                }
                Err(parse_error) => {
                    let err_source = parse_error.source.clone();
                    let mut exc = raise_parser_err(parse_error);
                    if let Some(source) = err_source {
                        if !self.config.skip_add_traceback {
                            exc = add_traceback(exc, py, &source.filename, "<kola>", source.lineno);
                        }
                    }
                    return Err(exc);
                }
            }
        }
    }
}
