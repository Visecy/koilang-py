//! Python exception bindings for KoiLang parsing errors
//!
//! This module provides Python exception bindings that map to the koicore::parser::error::ErrorInfo enum,
//! allowing each type of parsing error to be handled as a separate Python exception class.

use pyo3::exceptions::PyException;
use pyo3::prelude::*;

use koicore::parser::error::ParseError;

use crate::traceback::{PyParserLineSource, PyTracebackEntry};

/// Base class for all KoiLang parsing errors
///
/// This is the root exception class for all parsing errors that can occur
/// when parsing KoiLang files. It provides access to traceback information
/// and source location details for debugging parsing issues.
#[pyclass(name = "KoiParseError", subclass, extends = PyException, module = "koilang.core.error")]
pub struct PyParseError {
    /// Optional traceback entry containing detailed parsing context
    #[pyo3(get)]
    traceback: Option<PyTracebackEntry>,
    /// Optional source information containing file path and line number
    #[pyo3(get)]
    source: Option<PyParserLineSource>,
}

#[pymethods]
impl PyParseError {
    /// Get the line number where the error occurred (if available)
    #[getter]
    pub fn lineno(&self) -> Option<usize> {
        self.source.as_ref().map(|source| source.lineno)
    }

    #[getter]
    pub fn filename(&self) -> Option<String> {
        self.source.as_ref().map(|source| source.filename.clone())
    }

    /// Get the position (line, column) where the error occurred (if available)
    #[getter]
    pub fn position(&self) -> Option<(usize, usize)> {
        self.traceback.as_ref().map(|tb| { (tb.inner.lineno, tb.inner.column_range.0) })
    }
}

/// Exception thrown when there are syntax errors in the input
///
/// This error is raised when the parser encounters malformed KoiLang syntax
/// that cannot be processed. The error message will describe what was expected
/// and what was found instead.
#[pyclass(name = "KoiParserSyntaxError", extends = PyParseError, module = "koilang.core.error")]
pub struct KoiParserSyntaxError {
    /// Human-readable error message describing the syntax error
    message: String,
}

#[pymethods]
impl KoiParserSyntaxError {
    #[new]
    pub fn new(message: String, koi_tracebck: Option<PyTracebackEntry>, source: Option<PyParserLineSource>) -> (Self, PyParseError) {
        (
            Self {
                message: message,
            },
            PyParseError {
                traceback: koi_tracebck,
                source: source,
            },
        )
    }

    /// Get the error message
    #[getter]
    pub fn message(&self) -> &str {
        &self.message
    }

    pub fn __str__(&self) -> &str {
        &self.message
    }
}


/// Exception thrown when parser encounters unexpected input
///
/// This error is raised when the parser expects one type of token or structure
/// but encounters something different. The remaining input that caused the issue
/// is preserved for debugging purposes.
#[pyclass(name = "KoiParserUnexpectedInputError", extends = PyParseError, module = "koilang.core.error")]
pub struct KoiParserUnexpectedInputError {
    /// The remaining input that caused the unexpected input error
    remaining: String,
}

#[pymethods]
impl KoiParserUnexpectedInputError {
    #[new]
    pub fn new(
        remaining: String,
        koi_traceback: Option<PyTracebackEntry>,
        source: Option<PyParserLineSource>,
    ) -> (Self, PyParseError) {
        (
            Self {
                remaining: remaining,
            },
            PyParseError {
                traceback: koi_traceback,
                source: source,
            },
        )
    }

    /// Get the error message
    #[getter]
    pub fn message(&self) -> String {
        format!("Unexpected input: '{}'", self.remaining)
    }

    pub fn __str__(&self) -> String {
        self.message()
    }
}

/// Exception thrown when parser reaches unexpected end of input
///
/// This error is raised when the parser expects more input but encounters
/// the end of file unexpectedly. The error message describes what was expected
/// to be found.
#[pyclass(name = "KoiParserUnexpectedEofError", extends = PyParseError, module = "koilang.core.error")]
pub struct KoiParserUnexpectedEofError {
    /// Description of what was expected when EOF was encountered
    expected: String,
}

#[pymethods]
impl KoiParserUnexpectedEofError {
    #[new]
    pub fn new(
        expected: String,
        koi_tracebck: Option<PyTracebackEntry>,
        source: Option<PyParserLineSource>,
    ) -> (Self, PyParseError) {
        (
            Self {
                expected: expected,
            },
            PyParseError {
                traceback: koi_tracebck,
                source: source,
            },
        )
    }

    /// Get the error message
    #[getter]
    pub fn message(&self) -> String {
        format!("Unexpected end of input. Expected: {}", self.expected)
    }

    pub fn __str__(&self) -> String {
        self.message()
    }
}

/// Convert a ParseError to an appropriate Python exception
///
/// This function maps the internal ParseError to the corresponding Python
/// exception type based on the error information contained within it.
/// It handles different error types including syntax errors, unexpected input,
/// unexpected EOF, and IO errors.
pub fn raise_parser_err(error: Box<ParseError>) -> PyErr {
    match error.error_info {
        koicore::parser::error::ErrorInfo::SyntaxError { message } => {
            PyErr::new::<KoiParserSyntaxError, (String, Option<PyTracebackEntry>, Option<PyParserLineSource>)>((
                message,
                error.traceback.map(|tb| tb.into()),
                error.source.map(|source| source.into()),
            ))
        }
        koicore::parser::error::ErrorInfo::UnexpectedInput { remaining } => {
            PyErr::new::<KoiParserUnexpectedInputError, (String, Option<PyTracebackEntry>, Option<PyParserLineSource>)>((
                remaining,
                error.traceback.map(|tb| tb.into()),
                error.source.map(|source| source.into()),
            ))
        }
        koicore::parser::error::ErrorInfo::UnexpectedEof { expected } => {
            PyErr::new::<KoiParserUnexpectedEofError, (String, Option<PyTracebackEntry>, Option<PyParserLineSource>)>((
                expected,
                error.traceback.map(|tb| tb.into()),
                error.source.map(|source| source.into()),
            ))
        }
        koicore::parser::error::ErrorInfo::IoError { error } => {
            error.into()
        }
    }
}
