//! Python bindings for KoiLang command structures
//!
//! This module provides clean Python bindings that expose Rust commands
//! as natural Python objects without unnecessary wrapping.

use pyo3::{
    exceptions::PyValueError,
    prelude::*,
    types::{PyDict, PyList, PyTuple},
};

use koicore::command::{Command, CompositeValue, Parameter, Value};

/// Convert Python objects to Rust Value types
fn py_to_rs_value(obj: &Bound<'_, PyAny>) -> PyResult<Value> {
    if let Ok(int_val) = obj.extract::<i64>() {
        Ok(Value::Int(int_val))
    } else if let Ok(float_val) = obj.extract::<f64>() {
        Ok(Value::Float(float_val))
    } else if let Ok(string_val) = obj.extract::<String>() {
        Ok(Value::String(string_val))
    } else if let Ok(bool_val) = obj.extract::<bool>() {
        Ok(Value::Bool(bool_val))
    } else {
        Err(PyValueError::new_err(format!(
            "Unsupported type for Value conversion: {}",
            obj.get_type().name()?
        )))
    }
}

/// Convert Rust Value to Python object
fn rs_value_to_py<'py>(value: &Value, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
    match value {
        Value::Int(i) => Ok(i
            .into_pyobject(py)
            .map_err(Into::<PyErr>::into)?
            .into_any()),
        Value::Float(f) => Ok(f
            .into_pyobject(py)
            .map_err(Into::<PyErr>::into)?
            .into_any()),
        Value::String(s) => Ok(s
            .into_pyobject(py)
            .map_err(Into::<PyErr>::into)?
            .into_any()),
        Value::Bool(b) => Ok(
            b.into_pyobject(py).map(|b| Bound::clone(&b))
            .map_err(Into::<PyErr>::into)?
            .into_any(),
        ),
    }
}

/// Convert Python objects to Rust CompositeValue
fn py_to_rs_composite_value(obj: &Bound<'_, PyAny>) -> PyResult<CompositeValue> {
    // Try as list
    if let Ok(py_list) = obj.cast::<PyList>() {
        let mut values = Vec::new();
        for item in py_list {
            values.push(py_to_rs_value(&item)?);
        }
        Ok(CompositeValue::List(values))
    } else if
    // Try as dict
    let Ok(py_dict) = obj.cast::<PyDict>() {
        let mut items = Vec::new();
        for (key, value) in py_dict {
            let key_str = key.extract::<String>()?;
            let value_val = py_to_rs_value(&value)?;
            items.push((key_str, value_val));
        }
        Ok(CompositeValue::Dict(items))
    } else {
        // Treat as single value
        Ok(CompositeValue::Single(py_to_rs_value(obj)?))
    }
}

/// Convert Rust CompositeValue to Python object
fn rs_composite_value_to_py<'py>(
    value: &CompositeValue,
    py: Python<'py>,
) -> PyResult<Bound<'py, PyAny>> {
    match value {
        CompositeValue::Single(v) => rs_value_to_py(v, py),
        CompositeValue::List(values) => {
            let py_list = PyList::empty(py);
            for v in values {
                py_list.append(rs_value_to_py(v, py)?)?;
            }
            Ok(py_list.into_any())
        }
        CompositeValue::Dict(items) => {
            let py_dict = PyDict::new(py);
            for (k, v) in items {
                py_dict.set_item(k, rs_value_to_py(v, py)?).unwrap();
            }
            Ok(py_dict.into_any())
        }
    }
}

/// Convert Python objects to Rust Parameter
fn py_to_rs_parameter(obj: &Bound<'_, PyAny>) -> PyResult<Parameter> {
    // Check if it's a tuple with exactly 2 elements (name, value)
    if let Ok(py_tuple) = obj.cast::<PyTuple>() {
        if py_tuple.len() == 2 {
            let name = py_tuple.get_item(0)?.extract::<String>()?;
            let value = py_to_rs_composite_value(&py_tuple.get_item(1)?)?;
            return Ok(Parameter::Composite(name, value));
        }
    }

    // Otherwise treat as basic parameter
    Ok(Parameter::Basic(py_to_rs_value(obj)?))
}

/// Convert Rust Parameter to Python object
fn rs_parameter_to_py<'py>(param: &Parameter, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
    match param {
        Parameter::Basic(value) => rs_value_to_py(value, py),
        Parameter::Composite(name, value) => {
            let py_tuple = PyTuple::new(
                py,
                &[
                    name.into_pyobject(py)?.into_any(),
                    rs_composite_value_to_py(value, py)?,
                ],
            )?;
            Ok(py_tuple.into_any())
        }
    }
}

/// Python binding for KoiLang Command
///
/// Represents a complete KoiLang command with natural Python interface.
///
/// A command consists of a name and a list of parameters. Parameters can be:
/// - Basic values: int, float, str
/// - Composite parameters: tuple (name, value) where value can be single, list, or dict
///
/// This class provides convenient access to both positional args and named kwargs,
/// making it easy to work with KoiLang commands in Python code.
#[pyclass(name = "Command", module = "koilang.core.command", eq)]
#[derive(Clone, PartialEq)]
pub struct PyCommand {
    /// Internal Rust Command instance
    pub(crate) inner: Command,
}

#[pymethods]
impl PyCommand {
    /// Create a new command with the specified name and parameters
    ///
    /// Args:
    ///     name: The command name as a string
    ///     params: List of parameters, which can be:
    ///         - Basic values: int, float, str
    ///         - Composite parameters: tuple (name, value) where value can be single, list, or dict
    ///
    /// Returns:
    ///     A new Command instance
    ///
    /// Raises:
    ///     ValueError: If any parameter has an unsupported type
    #[new]
    #[pyo3(signature = (name, params=Vec::new()), text_signature = "(name: str, params: list[str | int | float | tuple[str, Any]] = [])")]
    pub fn new(name: String, params: Vec<Bound<'_, PyAny>>) -> PyResult<Self> {
        let mut rs_params = Vec::new();
        for param in params {
            rs_params.push(py_to_rs_parameter(&param)?);
        }

        Ok(Self {
            inner: Command::new(name, rs_params),
        })
    }

    /// Create a text command representing regular content
    ///
    /// Args:
    ///     content: The text content as a string
    ///
    /// Returns:
    ///     A new Command instance representing text content
    #[staticmethod]
    pub fn new_text(content: String) -> Self {
        Self {
            inner: Command::new_text(content),
        }
    }

    /// Create an annotation command
    ///
    /// Args:
    ///     content: The annotation content as a string
    ///
    /// Returns:
    ///     A new Command instance representing an annotation
    #[staticmethod]
    pub fn new_annotation(content: String) -> Self {
        Self {
            inner: Command::new_annotation(content),
        }
    }

    /// Create a number command with integer value and additional parameters
    ///
    /// Args:
    ///     value: The integer value for the number command
    ///     args: List of additional parameters for the command
    ///
    /// Returns:
    ///     A new Command instance representing a number command
    ///
    /// Raises:
    ///     ValueError: If any parameter has an unsupported type
    #[staticmethod]
    pub fn new_number(value: i64, args: Vec<Bound<'_, PyAny>>) -> PyResult<Self> {
        let mut rs_args = Vec::new();
        for arg in args {
            rs_args.push(py_to_rs_parameter(&arg)?);
        }

        Ok(Self {
            inner: Command::new_number(value, rs_args),
        })
    }

    /// Get the command name
    ///
    /// Returns:
    ///     The command name as a string
    #[getter]
    pub fn name(&self) -> String {
        self.inner.name.clone()
    }

    /// Get the command parameters as Python objects
    ///
    /// Returns:
    ///     List of all parameters as Python objects (ints, floats, strings, tuples, lists, dicts)
    #[getter]
    pub fn params<'py>(&self, py: Python<'py>) -> PyResult<Vec<Bound<'py, PyAny>>> {
        self.inner
            .params
            .iter()
            .map(|param| rs_parameter_to_py(param, py))
            .collect()
    }

    /// Get the command args (basic value parameters)
    ///
    /// Returns:
    ///     List of basic value parameters (ints, floats, strings) excluding composite parameters
    #[getter]
    pub fn args<'py>(&self, py: Python<'py>) -> PyResult<Vec<Bound<'py, PyAny>>> {
        let mut args = Vec::new();
        for param in &self.inner.params {
            if let Parameter::Basic(value) = param {
                args.push(rs_value_to_py(value, py)?);
            }
        }
        Ok(args)
    }

    /// Get the command kwargs (composite parameters as dict)
    ///
    /// Returns:
    ///     Dictionary mapping parameter names to their composite values (single, list, or dict)
    #[getter]
    pub fn kwargs<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let kwargs_dict = PyDict::new(py);
        for param in &self.inner.params {
            if let Parameter::Composite(name, value) = param {
                kwargs_dict
                    .set_item(name, rs_composite_value_to_py(value, py)?)
                    .unwrap();
            }
        }
        Ok(kwargs_dict)
    }

    /// Set the command name
    ///
    /// Args:
    ///     value: The new command name as a string
    #[setter]
    pub fn set_name(&mut self, name: String) {
        self.inner.name = name;
    }

    /// Set the command parameters from Python objects
    ///
    /// Args:
    ///     params: List of new parameters (same types as accepted by __init__)
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     ValueError: If any parameter has an unsupported type
    #[setter]
    pub fn set_params(&mut self, params: Vec<Bound<'_, PyAny>>) -> PyResult<()> {
        let mut rs_params = Vec::new();
        for param in params {
            rs_params.push(py_to_rs_parameter(&param)?);
        }
        self.inner.params = rs_params;
        Ok(())
    }

    /// Add a parameter to the command
    ///
    /// Args:
    ///     param: Parameter to add (same types as accepted in params list)
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     ValueError: If parameter has an unsupported type
    pub fn add_param(&mut self, param: Bound<'_, PyAny>) -> PyResult<()> {
        let rs_param = py_to_rs_parameter(&param)?;
        self.inner.params.push(rs_param);
        Ok(())
    }

    /// Get a string representation of the command
    ///
    /// Returns:
    ///     String representation in format: Command('name', [param1, param2, ...])
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        let params_repr = self
            .params(py)?
            .iter()
            .map(|param| param.repr().and_then(|repr| repr.extract::<String>()))
            .collect::<PyResult<Vec<String>>>()?;
        Ok(format!(
            "Command('{}', [{}])",
            self.name(),
            params_repr.join(", ")
        ))
    }

    /// Convert command to string
    ///
    /// Returns:
    ///     String representation of the command in KoiLang format
    fn __str__(&self) -> String {
        self.inner.to_string()
    }
}

impl From<Command> for PyCommand {
    fn from(command: Command) -> Self {
        Self { inner: command }
    }
}

impl From<&PyCommand> for Command {
    fn from(py_command: &PyCommand) -> Self {
        py_command.inner.clone()
    }
}
