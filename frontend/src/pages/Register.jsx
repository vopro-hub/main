import { useState, useContext, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import { api } from "../api";
import "../static/Register.css";

const passwordRules = {
  length: (pw) => pw.length >= 8,
  letter: (pw) => /[a-zA-Z]/.test(pw),
  number: (pw) => /\d/.test(pw),
  symbol: (pw) => /[^a-zA-Z0-9]/.test(pw),
};

const isPasswordValid = (pw) => {
  if (!passwordRules.length(pw)) return false;
  let count = 0;
  if (passwordRules.letter(pw)) count++;
  if (passwordRules.number(pw)) count++;
  if (passwordRules.symbol(pw)) count++;
  return count >= 2;
};

const calculateStrength = (pw) => {
  let score = 0;
  if (passwordRules.length(pw)) score++;
  if (passwordRules.letter(pw)) score++;
  if (passwordRules.number(pw)) score++;
  if (passwordRules.symbol(pw)) score++;
  return score;
};

const Register = () => {
  const [formData, setFormData] = useState({
    username: "",
    first_name: "",
    last_name: "",
    office_name: "",
    email: "",
    city: "",
    password: "",
    confirmPassword: "",
  });

  const [cities, setCities] = useState([]);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const { register } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCities = async () => {
      try {
        const res = await api.get("/workspace/cities/");
        setCities(res.data);
      } catch (err) {
        console.error("Failed to load cities", err);
      }
    };
    fetchCities();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: "" });
  };

  const validate = () => {
    const errs = {};
    const { username, email, city, password, confirmPassword, first_name, last_name, office_name } = formData;
    if (!first_name.trim()) errs.first_name = "First name is required.";
    if (!last_name.trim()) errs.last_name = "Last name is required.";
    if (!office_name.trim()) errs.office_name = "Office name is required.";
    if (!username.trim()) errs.username = "Username is required.";
    if (!email.includes("@")) errs.email = "Invalid email address.";
    if (!city) errs.city = "Please select a city.";
    if (!isPasswordValid(password)) errs.password = "Password is too weak.";
    if (password !== confirmPassword)
      errs.confirmPassword = "Passwords do not match.";
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      await register(formData);

      navigate("/office");
    } catch (error) {
      console.error("Registration error:", error);

      const fieldErrors = {};
      const apiError = error.response?.data;

      if (apiError) {
        // Loop through backend response fields
        for (const key in apiError) {
          if (Array.isArray(apiError[key])) {
            fieldErrors[key] = apiError[key][0];
          } else if (typeof apiError[key] === "string") {
            fieldErrors[key] = apiError[key];
          }
        }
        setErrors(fieldErrors);
        setMessage(apiError.error || apiError.detail || "Registration failed.");
      } else {
        setMessage("An unexpected error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  const strength = calculateStrength(formData.password);
  const progressColors = ["#e74c3c", "#f39c12", "#f1c40f", "#2ecc71"];
  const progressPercent = (strength / 4) * 100;

  const isFormInvalid =
    !formData.username ||
    !formData.first_name ||
    !formData.last_name ||
    !formData.office_name ||
    !formData.email ||
    !formData.city ||
    !formData.password ||
    !formData.confirmPassword ||
    !isPasswordValid(formData.password);

  return (
    <div className="register-container">
      <form onSubmit={handleSubmit} className="register-form">
        <h2>Create Account</h2>
        <label htmlFor="firstname">Firt name:</label>
        <input
          name="first_name"
          placeholder="First Name"
          onChange={handleChange}
          value={formData.first_name}
          className="register-input"
        />
        {errors.first_name && <p className="error-message">{errors.first_name}</p>}
        <label htmlFor="lastname">Last name:</label>
        <input
          name="last_name"
          placeholder="Last Name"
          onChange={handleChange}
          value={formData.last_name}
          className="register-input"
        />
        {errors.last_name && <p className="error-message">{errors.last_name}</p>}
        <label htmlFor="officename">Office name:</label>
        <input
          name="office_name"
          placeholder="Office Name"
          onChange={handleChange}
          value={formData.office_name}
          className="register-input"
        />
        {errors.office_name && <p className="error-message">{errors.office_name}</p>}
        <label htmlFor="username">Username:</label>
        <input
          name="username"
          placeholder="Username"
          onChange={handleChange}
          value={formData.username}
          className="register-input"
        />
        {errors.username && <p className="error-message">{errors.username}</p>}
        <label htmlFor="email">Email:</label>
        <input
          name="email"
          placeholder="Email"
          onChange={handleChange}
          value={formData.email}
          className="register-input"
        />
        {errors.email && <p className="error-message">{errors.email}</p>}
        <label htmlFor="city">City:</label>
        <select
          name="city"
          value={formData.city}
          onChange={handleChange}
          className="register-input"
        >
          <option value="">-- Choose City --</option>
          {cities.map((c) => (
            <option key={c.id} value={c.id}>
              {c.city}, {c.country}
            </option>
          ))}
        </select>
        {errors.city && <p className="error-message">{errors.city}</p>}
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          name="password"
          placeholder="Password"
          onChange={handleChange}
          value={formData.password}
          className="register-input"
        />
        {errors.password && <p className="error-message">{errors.password}</p>}

        {formData.password && (
          <div className="password-strength">
            <div
              className="progress-bar"
              style={{
                width: `${progressPercent}%`,
                backgroundColor: progressColors[strength - 1] || "#ddd",
                height: "6px",
                borderRadius: "4px",
                margin: "5px",
              }}
            />
          </div>
        )}
        <label htmlFor="comfirmpassword">Comfirm password:</label>
        <input
          type="password"
          name="confirmPassword"
          placeholder="Confirm Password"
          onChange={handleChange}
          value={formData.confirmPassword}
          className="register-input"
        />
        {errors.confirmPassword && (
          <p className="error-message">{errors.confirmPassword}</p>
        )}

        <button
          type="submit"
          disabled={loading || isFormInvalid}
          className="register-button"
        >
          {loading ? "Registering..." : "Register"}
        </button>

        {message && <p className="error-message">{message}</p>}

        <p>
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </form>
    </div>
  );
};

export default Register;
