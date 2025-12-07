//! Python exception bindings for KoiLang parsing errors
//!
//! This module provides Python exception bindings that map to the koicore::parser::error::ErrorInfo enum,
//! allowing each type of parsing error to be handled as a separate Python exception class.

use pyo3::exceptions::PyException;
use pyo3::prelude::*;

use koicore::parser::error::{ ParseError, ParserLineSource };

use crate::traceback::{PyParserLineSource, PyTracebackEntry};

impl From<ParserLineSource> for PyParserLineSource {
    fn from(source: ParserLineSource) -> Self {
        Self {
            filename: source.filename,
            lineno: source.lineno,
            text: Some(source.text),
        }
    }
}

/// Base class for all KoiLang parsing errors
#[pyclass(name = "KoiParseError", subclass, extends = PyException)]
pub struct PyParseError {
    #[pyo3(get)]
    traceback: Option<PyTracebackEntry>,
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

/// KoiParserSyntaxError - thrown when there are syntax errors in the input
#[pyclass(name = "KoiParserSyntaxError", extends = PyParseError)]
pub struct KoiParserSyntaxError {
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


/// KoiParserUnexpectedInputError - thrown when parser encounters unexpected input
#[pyclass(name = "KoiParserUnexpectedInputError", extends = PyParseError)]
pub struct KoiParserUnexpectedInputError {
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

/// KoiParserUnexpectedEofError - thrown when parser reaches unexpected end of input
#[pyclass(name = "KoiParserUnexpectedEofError", extends = PyParseError)]
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
