//! Python bindings for KoiLang writer module
//!
//! This module provides Python bindings for the koicore writer functionality,
//! allowing Python code to generate KoiLang text from parsed commands.

use std::collections::HashMap;

use pyo3::exceptions::PyValueError;
use pyo3::{
    prelude::*,
    types::{PyAny, PyDict, PyType},
};

use koicore::writer::{FormatterOptions, NumberFormat, ParamFormatSelector, Writer, WriterConfig};

use crate::io::PyIoWrapper;

/// Number format options for command parameter formatting
///
/// This enum defines the different numeric formats that can be used when
/// writing commands to KoiLang files. It controls how numeric values are
/// represented in the output.
#[pyclass(name = "NumberFormat", module = "koilang.core.writer", eq, eq_int)]
#[derive(Debug, PartialEq, Clone, Copy)]
pub enum PyNumberFormat {
    /// Unset number format (default) - uses natural representation
    #[pyo3(name = "UNKNOWN")]
    Unknown,
    /// Decimal format (e.g., 42)
    #[pyo3(name = "DECIMAL")]
    Decimal,
    /// Hexadecimal format (e.g., 0x2A)
    #[pyo3(name = "HEX")]
    Hex,
    /// Octal format (e.g., 052)
    #[pyo3(name = "OCTAL")]
    Octal,
    /// Binary format (e.g., 0b101010)
    #[pyo3(name = "BINARY")]
    Binary,
}

impl From<PyNumberFormat> for NumberFormat {
    fn from(py_format: PyNumberFormat) -> Self {
        match py_format {
            PyNumberFormat::Unknown => NumberFormat::Unknown,
            PyNumberFormat::Decimal => NumberFormat::Decimal,
            PyNumberFormat::Hex => NumberFormat::Hex,
            PyNumberFormat::Octal => NumberFormat::Octal,
            PyNumberFormat::Binary => NumberFormat::Binary,
        }
    }
}

impl From<NumberFormat> for PyNumberFormat {
    fn from(format: NumberFormat) -> Self {
        match format {
            NumberFormat::Unknown => PyNumberFormat::Unknown,
            NumberFormat::Decimal => PyNumberFormat::Decimal,
            NumberFormat::Hex => PyNumberFormat::Hex,
            NumberFormat::Octal => PyNumberFormat::Octal,
            NumberFormat::Binary => PyNumberFormat::Binary,
        }
    }
}

/// Selector for parameter format configuration
///
/// This class provides ways to select specific parameters for custom formatting
/// rules. You can select parameters either by their position (0-based index)
/// in the parameter list or by their name for composite parameters.
#[pyclass(name = "ParamFormatSelector", module = "koilang.core.writer")]
#[derive(Debug, PartialEq, Clone)]
pub enum PyParamFormatSelector {
    /// Select parameter by position (0-based index)
    Position(usize),
    /// Select composite parameter by name
    Name(String),
}

#[pymethods]
impl PyParamFormatSelector {
    /// Create a selector by position index
    ///
    /// Args:
    ///     position: 0-based position in the parameter list
    ///
    /// Returns:
    ///     New ParamFormatSelector instance
    #[classmethod]
    pub fn by_position(_cls: &Bound<'_, PyType>, position: usize) -> Self {
        Self::Position(position)
    }

    /// Create a selector by parameter name
    ///
    /// Args:
    ///     name: Name of the composite parameter
    ///
    /// Returns:
    ///     New ParamFormatSelector instance
    #[classmethod]
    pub fn by_name(_cls: &Bound<'_, PyType>, name: &str) -> Self {
        Self::Name(name.to_string())
    }

    /// Check equality with another ParamFormatSelector
    ///
    /// Args:
    ///     other: Another ParamFormatSelector to compare with
    ///
    /// Returns:
    ///     True if both selectors are equivalent
    pub fn __eq__(&self, other: &Self) -> bool {
        self == other
    }

    /// Get hash value for dictionary keys
    ///
    /// Returns:
    ///     Hash value for use in dictionaries and sets
    pub fn __hash__(&self) -> u64 {
        match self {
            Self::Position(pos) => (*pos as u64).wrapping_mul(31),
            Self::Name(name) => name
                .as_bytes()
                .iter()
                .fold(0u64, |acc, &b| acc.wrapping_mul(31).wrapping_add(b as u64)),
        }
    }

    /// Get string representation
    ///
    /// Returns:
    ///     String representation in format: ParamFormatSelector.Position(n) or ParamFormatSelector.Name("name")
    pub fn __str__(&self) -> String {
        match self {
            Self::Position(pos) => format!("ParamFormatSelector.Position({})", pos),
            Self::Name(name) => format!("ParamFormatSelector.Name({:?})", name),
        }
    }
}

impl From<PyParamFormatSelector> for ParamFormatSelector {
    fn from(py_selector: PyParamFormatSelector) -> Self {
        match py_selector {
            PyParamFormatSelector::Position(pos) => ParamFormatSelector::Position(pos),
            PyParamFormatSelector::Name(name) => ParamFormatSelector::Name(name),
        }
    }
}

/// Python bindings for FormatterOptions
/// Formatting options for command output
///
/// This structure defines all the formatting options that can be applied when
/// writing KoiLang commands to output. It controls indentation, whitespace,
/// number formatting, and other presentation aspects.
#[derive(Debug, FromPyObject)]
pub struct PyFormatterOptions {
    /// Number of spaces to use for indentation
    pub indent: usize,
    /// Whether to use tabs for indentation instead of spaces
    pub use_tabs: bool,
    /// Whether to add a newline before the command
    pub newline_before: bool,
    /// Whether to add a newline after the command
    pub newline_after: bool,
    /// Whether to use compact formatting (minimal whitespace)
    pub compact: bool,
    /// Whether to force quotes for names that match variable naming rules
    pub force_quotes_for_vars: bool,
    /// Format to use for numeric values
    pub number_format: PyNumberFormat,
    /// Whether to add a newline before this specific parameter
    pub newline_before_param: bool,
    /// Whether to add a newline after this specific parameter
    pub newline_after_param: bool,
    /// Whether to override the base options completely
    pub should_override: bool,
}

impl From<PyFormatterOptions> for FormatterOptions {
    fn from(py_options: PyFormatterOptions) -> Self {
        FormatterOptions {
            indent: py_options.indent,
            use_tabs: py_options.use_tabs,
            newline_before: py_options.newline_before,
            newline_after: py_options.newline_after,
            compact: py_options.compact,
            force_quotes_for_vars: py_options.force_quotes_for_vars,
            number_format: NumberFormat::from(py_options.number_format),
            newline_before_param: py_options.newline_before_param,
            newline_after_param: py_options.newline_after_param,
            should_override: py_options.should_override,
        }
    }
}

/// Python bindings for WriterConfig
/// Configuration structure for Writer behavior
///
/// This structure holds all configuration options that control how the writer
/// formats KoiLang output. It includes global formatting options that apply to
/// all commands, plus command-specific overrides for special formatting needs.
#[derive(FromPyObject)]
pub struct PyWriterConfig {
    /// Global formatting options
    pub global_options: PyFormatterOptions,
    /// Command-specific formatting options
    pub command_options: HashMap<String, PyFormatterOptions>,
    /// Command threshold (number of # required for commands)
    pub command_threshold: usize,
}

impl From<PyWriterConfig> for WriterConfig {
    fn from(py_config: PyWriterConfig) -> Self {
        Self {
            global_options: FormatterOptions::from(py_config.global_options),
            command_options: py_config
                .command_options
                .into_iter()
                .map(|(k, v)| (k, FormatterOptions::from(v)))
                .collect(),
            command_threshold: py_config.command_threshold,
        }
    }
}

/// Python bindings for Writer
///
/// This class provides functionality to write KoiLang commands to output streams
/// with various formatting options. It handles indentation, number formatting,
/// and can apply custom formatting rules for specific commands or parameters.
#[pyclass(name = "Writer", module = "koilang.core.writer")]
pub struct PyWriter {
    /// Internal Rust Writer instance
    // We need to use a Box to allow the writer to live beyond the constructor
    pub writer: Writer<PyIoWrapper>,
}

#[pymethods]
impl PyWriter {
    /// Create a new Writer from a Python file-like object or string IO
    ///
    /// Args:
    ///     py_file: Python file-like object with write() and flush() methods
    ///     config: Optional writer configuration
    ///
    /// Returns:
    ///     New Writer instance
    ///
    /// Raises:
    ///     TypeError: If the object doesn't have required write/flush methods
    #[new]
    #[pyo3(signature = (py_file, config=None))]
    pub fn new(py_file: Bound<'_, PyAny>, config: Option<PyWriterConfig>) -> PyResult<Self> {
        // Create a PyIoWrapper from the Python file-like object
        let py_write_wrapper = PyIoWrapper::new(py_file)?;

        // Create WriterConfig
        let writer_config = config.map(|c| WriterConfig::from(c)).unwrap_or_default();

        Ok(Self { writer: Writer::new(py_write_wrapper, writer_config) })
    }

    /// Write a command using the default formatting options
    ///
    /// Args:
    ///     command: Command object to write
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     ValueError: If writing fails
    pub fn write_command(&mut self, _command: Bound<'_, PyAny>) -> PyResult<()> {
        // For now, we'll just write a placeholder message
        // We need to add a method to PyCommand to get the inner command
        // or modify PyCommand to expose the necessary functionality
        self.writer
            .newline()
            .map_err(|e| PyValueError::new_err(format!("Failed to write newline: {}", e)))
    }

    /// Write a command with custom formatting options
    ///
    /// Args:
    ///     command: Command object to write
    ///     options: Optional custom formatting options
    ///     param_options: Optional parameter-specific formatting options
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     ValueError: If writing fails
    pub fn write_command_with_options(
        &mut self,
        _command: Bound<'_, PyAny>,
        _options: Option<Bound<'_, PyAny>>,
        _param_options: Option<Bound<'_, PyDict>>,
    ) -> PyResult<()> {
        // For now, we'll just write a placeholder message
        self.writer
            .newline()
            .map_err(|e| PyValueError::new_err(format!("Failed to write newline: {}", e)))
    }

    /// Increase the indentation level by 1
    ///
    /// This affects subsequent command writes by adding one level of indentation.
    pub fn inc_indent(&mut self) {
        self.writer.inc_indent();
    }

    /// Decrease the indentation level by 1, but not below 0
    ///
    /// Ensures indentation never goes below zero.
    pub fn dec_indent(&mut self) {
        self.writer.dec_indent();
    }

    /// Get the current indentation level
    ///
    /// Returns:
    ///     Current indentation level as integer
    pub fn get_indent(&self) -> usize {
        self.writer.get_indent()
    }

    /// Write a newline character
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     ValueError: If writing fails
    pub fn newline(&mut self) -> PyResult<()> {
        self.writer
            .newline()
            .map_err(|e| PyValueError::new_err(format!("Failed to write newline: {}", e)))
    }
}
