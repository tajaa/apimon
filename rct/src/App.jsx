import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [coworkers, setCoworkers] = useState([]);
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [department, setDepartment] = useState("");
  const [salary, setSalary] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");
  const [departments, setDepartments] = useState([]);
  const [selectedDepartment, setSelectedDepartment] = useState("");

  useEffect(() => {
    fetchCoworkers();
    fetchDepartments();
  }, []);

  const fetchCoworkers = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/coworkers?search=${search}&department=${selectedDepartment}`,
      );
      if (!response.ok) {
        throw new Error("Failed to fetch coworkers");
      }
      const data = await response.json();
      setCoworkers(data);
    } catch (error) {
      setError("Error fetching coworkers: " + error.message);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await fetch("http://localhost:8000/departments");
      if (!response.ok) {
        throw new Error("Failed to fetch departments");
      }
      const data = await response.json();
      setDepartments(data.departments);
    } catch (error) {
      setError("Error fetching departments: " + error.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const response = await fetch("http://localhost:8000/coworkers", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          role,
          department,
          salary: parseFloat(salary),
        }),
      });
      if (!response.ok) {
        throw new Error("Failed to create coworker");
      }
      setName("");
      setRole("");
      setDepartment("");
      setSalary("");
      setMessage("Coworker added successfully!");
      fetchCoworkers();
    } catch (error) {
      setError("Error creating coworker: " + error.message);
    }
  };

  return (
    <div className="App">
      <h1>Coworker Management</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {message && <p style={{ color: "green" }}>{message}</p>}
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          type="text"
          placeholder="Role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          required
        />
        <input
          type="text"
          placeholder="Department"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          required
        />
        <input
          type="number"
          placeholder="Salary"
          value={salary}
          onChange={(e) => setSalary(e.target.value)}
          required
        />
        <button type="submit">Add Coworker</button>
      </form>
      <div>
        <input
          type="text"
          placeholder="Search coworkers"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          value={selectedDepartment}
          onChange={(e) => setSelectedDepartment(e.target.value)}
        >
          <option value="">All Departments</option>
          {departments.map((dept) => (
            <option key={dept} value={dept}>
              {dept}
            </option>
          ))}
        </select>
        <button onClick={fetchCoworkers}>Search</button>
      </div>
      <h2>Coworkers</h2>
      <ul>
        {coworkers.map((coworker) => (
          <li key={coworker.id}>
            {coworker.name} - {coworker.role} - {coworker.department} - $
            {coworker.salary}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
