use pyo3::prelude::*;

pub mod command;
pub mod parser;
pub mod traceback;
pub mod error;
pub mod io;
pub mod writer;

/// A Python module implemented in Rust.
#[pymodule]
mod core {
    #[pymodule_export]
    use super::command::PyCommand;

    #[pymodule_export]
    use super::parser::PyParser;
    
    #[pymodule_export]
    use super::traceback::{PyTracebackEntry, PyParserLineSource};
    
    #[pymodule_export]
    use super::error::{KoiParserSyntaxError, KoiParserUnexpectedInputError, KoiParserUnexpectedEofError, PyParseError};
    
    #[pymodule_export]
    use super::writer::{PyNumberFormat, PyParamFormatSelector, PyWriter};
}
