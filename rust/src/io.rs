//! Python IO object wrappers for Rust
//!
//! This module provides wrappers that allow Python objects to be used where Rust
//! `std::io::Read` and `std::io::Write` traits are expected.

use pyo3::prelude::*;
use std::{
    io::{self, Read, Write},
    ops::Deref,
};

/// Wraps a Python object to implement Rust's `std::io::Read` and `std::io::Write` traits.
///
/// This allows Python objects with appropriate methods (like file objects,
/// StringIO, etc.) to be used with Rust's IO ecosystem, including being
/// wrapped in `io::BufReader` for reading or used directly for writing.
pub struct PyIoWrapper {
    /// The wrapped Python object
    py_object: Py<PyAny>,
    /// Internal buffer for read operations to handle byte/char mismatch
    read_buffer: Vec<u8>,
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
            read_buffer: Vec::new(),
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
        // First, try to satisfy the read from the internal buffer
        if !self.read_buffer.is_empty() {
            let copy_len = std::cmp::min(buf.len(), self.read_buffer.len());
            buf[..copy_len].copy_from_slice(&self.read_buffer[..copy_len]);
            self.read_buffer.drain(..copy_len);
            return Ok(copy_len);
        }

        let size = buf.len();

        Python::attach(|py| {
            let py_obj = self.py_object.bind(py);

            // Call the Python read method - it returns a str in text mode
            let result = py_obj
                .call_method1("read", (size,))
                .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;

            // Extract string from the result
            let text: String = result
                .extract()
                .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e))?;

            if text.is_empty() {
                return Ok(0);
            }

            let bytes = text.into_bytes();
            let copy_len = std::cmp::min(buf.len(), bytes.len());
            buf[..copy_len].copy_from_slice(&bytes[..copy_len]);

            // If we read more bytes than the buffer can hold, store the rest
            if bytes.len() > buf.len() {
                self.read_buffer.extend_from_slice(&bytes[copy_len..]);
            }

            Ok(copy_len)
        })
    }
}

impl Write for PyIoWrapper {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        // Convert the buffer to a UTF-8 string
        let text = std::str::from_utf8(buf).map_err(|e| {
            io::Error::new(
                io::ErrorKind::InvalidData,
                format!("Invalid UTF-8 data for string-based writing: {}", e),
            )
        })?;

        Python::attach(|py| {
            let py_obj = self.py_object.bind(py);

            // Call the Python write method
            let result = py_obj
                .call_method1("write", (text,))
                .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;

            // Extract the number of characters written
            let _written: usize = result
                .extract()
                .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e))?;

            // Since we processed the whole buffer as one string, we return the byte length
            Ok(buf.len())
        })
    }

    fn flush(&mut self) -> io::Result<()> {
        Python::attach(|py| {
            let py_obj = self.py_object.bind(py);

            // Call the Python flush method
            py_obj
                .call_method0("flush")
                .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;

            Ok(())
        })
    }
}
