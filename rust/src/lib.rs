use pyo3::prelude::*;

pub mod command;
pub mod error;
pub mod io;
pub mod parser;
pub mod traceback;
pub mod writer;

/// A Python module implemented in Rust.
#[pymodule]
mod core {
    #[pymodule_export]
    use super::command::PyCommand;

    #[pymodule_export]
    use super::parser::PyParser;

    #[pymodule_export]
    use super::traceback::{PyParserLineSource, PyTracebackEntry};

    #[pymodule_export]
    use super::error::{
        KoiParserSyntaxError, KoiParserUnexpectedEofError, KoiParserUnexpectedInputError,
        PyParseError,
    };

    #[pymodule_export]
    use super::writer::{PyParamFormatSelector, PyWriter};
}
