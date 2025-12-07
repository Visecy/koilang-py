//! Python bindings for KoiLang traceback handling
//!
//! This module provides Python bindings for koicore traceback functionality,
//! allowing Python code to access detailed parsing error information including
//! file locations, line numbers, column positions, and parsing context.

use std::ffi::CString;

use pyo3::prelude::*;
use pyo3::ffi;

use koicore::parser::traceback::TracebackEntry;
use pyo3::types::PyDict;

#[pyclass(name = "KoiParserLineSource")]
#[derive(Clone)]
pub struct PyParserLineSource {
    /// Source file path
    /// 
    /// The path to the file where the line originated from.
    /// This could be a file path, URL, or any other identifier for the source.
    #[pyo3(get)]
    pub filename: String,
    
    /// Line number in the source file
    /// 
    /// The line number where the error occurred, starting from 1.
    #[pyo3(get)]
    pub lineno: usize,
    
    /// The input line content
    /// 
    /// The actual text content of the line where the error occurred.
    /// This is used to display the problematic code in error messages.
    #[pyo3(get)]
    pub text: Option<String>,
}

#[pymethods]
impl PyParserLineSource {
    #[new]
    pub fn new(filename: String, lineno: usize, text: Option<String>) -> Self {
        Self { filename, lineno, text }
    }

    pub fn __repr__(&self) -> String {
        format!("KoiParserLineSource(filename='{}', lineno={})",
                self.filename, self.lineno)
    }
}

/// Python binding for TracebackEntry - exposes all traceback information for Python access
#[pyclass(name = "TracebackEntry")]
#[derive(Clone)]
pub struct PyTracebackEntry {
    pub(super) inner: TracebackEntry,
}

#[pymethods]
impl PyTracebackEntry {
    #[new]
    pub fn new(lineno: usize, start_column: usize, end_column: usize, context: String) -> Self {
        Self { inner: TracebackEntry::new(lineno, (start_column, end_column), context) }
    }

    /// Get the line number where this traceback point occurred
    #[getter]
    pub fn lineno(&self) -> usize {
        self.inner.lineno
    }

    /// Get the column range where this traceback point occurred
    /// Returns a tuple (start_column, end_column)
    #[getter]
    pub fn column_range(&self) -> (usize, usize) {
        self.inner.column_range
    }

    /// Get the context description for this traceback point
    #[getter]
    pub fn context(&self) -> String {
        self.inner.context.clone()
    }

    /// Get the child traceback entries
    /// Returns a list of TracebackEntry objects
    #[getter]
    pub fn children(&self) -> Vec<PyTracebackEntry> {
        self.inner.children
            .iter()
            .map(|child| PyTracebackEntry { inner: child.clone() })
            .collect()
    }

    /// Get the start column for convenience
    pub fn start_column(&self) -> usize {
        self.inner.column_range.0
    }

    /// Get the end column for convenience
    pub fn end_column(&self) -> usize {
        self.inner.column_range.1
    }

    /// Check if this traceback entry has children
    pub fn has_children(&self) -> bool {
        !self.inner.children.is_empty()
    }

    pub fn __repr__(&self) -> String {
        format!("TracebackEntry(lineno={}, column_range={:?}, context={}, len(children)={})",
                self.inner.lineno, self.inner.column_range, self.inner.context, self.inner.children.len())
    }

    pub fn __str__(&self) -> String {
        self.inner.to_string().trim_end().to_owned()
    }
}

impl From<TracebackEntry> for PyTracebackEntry {
    fn from(traceback: TracebackEntry) -> Self {
        PyTracebackEntry { inner: traceback }
    }
}

impl From<&TracebackEntry> for PyTracebackEntry {
    fn from(traceback: &TracebackEntry) -> Self {
        PyTracebackEntry { inner: traceback.clone() }
    }
}

pub fn add_traceback(exc: PyErr, py: Python<'_>, filename: &str, funcname: &str, lineno: usize) -> PyErr {
    let globals = PyDict::new(py);
    let filename = match CString::new(filename) {
        Ok(filename) => filename,
        Err(_) => return PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid filename"),
    };
    let funcname = match CString::new(funcname) {
        Ok(funcname) => funcname,
        Err(_) => return PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid funcname"),
    };
    unsafe {
        let code = ffi::PyCode_NewEmpty(
            filename.as_ptr(),
            funcname.as_ptr(),
            lineno as std::ffi::c_int,
        );
        if code.is_null() {
            return PyErr::fetch(py);
        }
        let frame = ffi::PyFrame_New(
            ffi::PyThreadState_Get(),
            code,
            globals.as_ptr(),
            std::ptr::null_mut(),
        );
        if frame.is_null() {
            ffi::Py_DecRef(code as *mut ffi::PyObject);
            return PyErr::fetch(py);
        }
        exc.restore(py);
        ffi::PyTraceBack_Here(frame);
        ffi::Py_DecRef(frame as *mut ffi::PyObject);
        ffi::Py_DecRef(code as *mut ffi::PyObject);
    }
    PyErr::fetch(py)
}
