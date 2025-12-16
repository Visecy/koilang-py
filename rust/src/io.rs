//! Python IO object wrappers for Rust
//!
//! This module provides wrappers that allow Python objects to be used where Rust
//! `std::io::Read` and `std::io::Write` traits are expected.

use pyo3::{prelude::*, types::PyBytes};
use std::{io::{self, Read, Write}, ops::Deref};

/// Wraps a Python object to implement Rust's `std::io::Read` and `std::io::Write` traits.
///
/// This allows Python objects with appropriate methods (like file objects,
/// StringIO, etc.) to be used with Rust's IO ecosystem, including being
/// wrapped in `io::BufReader` for reading or used directly for writing.
pub struct PyIoWrapper {
    /// The wrapped Python object
    py_object: Py<PyAny>,
}

impl PyIoWrapper {
    /// Create a new `PyIoWrapper` from a Python object.
    ///
    /// Args:
    ///     py_object: Python object to wrap
    ///
    /// Returns:
    ///     New PyIoWrapper instance
    #[inline]
    pub fn new(py_object: Bound<'_, PyAny>) -> PyResult<Self> {
        Ok(Self {
            py_object: py_object.into(),
        })
    }
}

impl Deref for PyIoWrapper {
    type Target = Py<PyAny>;
    
    #[inline]
    fn deref(&self) -> &Self::Target {
        &self.py_object
    }
}

impl Read for PyIoWrapper {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        let size = buf.len();
        
        Python::attach(|py| {
            let py_obj = self.py_object.bind(py);
            
            // Call the Python read method
            let result = py_obj
                .call_method1("read", (size,))
                .map_err(|e| {
                    io::Error::new(
                        io::ErrorKind::Other,
                        e
                    )
                })?;
            
            // Extract bytes from the result
            let bytes: Vec<u8> = result.extract().map_err(|e| {
                io::Error::new(
                    io::ErrorKind::InvalidData,
                    e
                )
            })?;
            
            // Copy the bytes to the buffer
            let copy_len = bytes.len().min(size);
            buf[..copy_len].copy_from_slice(&bytes[..copy_len]);
            
            Ok(copy_len)
        })
    }
}

impl Write for PyIoWrapper {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        Python::attach(|py| {
            let py_obj = self.py_object.bind(py);
            
            // Convert the buffer to a Python bytes object
            let py_bytes = PyBytes::new(py, buf);
            
            // Call the Python write method
            let result = py_obj
                .call_method1("write", (py_bytes,))
                .map_err(|e| {
                    io::Error::new(
                        io::ErrorKind::Other,
                        e
                    )
                })?;
            
            // Extract the number of bytes written
            let written: usize = result.extract().map_err(|e| {
                io::Error::new(
                    io::ErrorKind::InvalidData,
                    e
                )
            })?;
            
            Ok(written)
        })
    }
    
    fn flush(&mut self) -> io::Result<()> {
        Python::attach(|py| {
            let py_obj = self.py_object.bind(py);
            
            // Call the Python flush method
            py_obj
                .call_method0("flush")
                .map_err(|e| {
                    io::Error::new(
                        io::ErrorKind::Other,
                        format!("Python flush() failed: {}", e)
                    )
                })?;
            
            Ok(())
        })
    }
}
