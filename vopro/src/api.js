// src/api.js
import axios from "axios";
axios.defaults.withCredentials = true;
const baseURL = "http://127.0.0.1:8000/api"; // Django backend URL

// create axios instance
const api = axios.create({
  baseURL: baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});





// attach token if available
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("token");
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// Public API instance (NO auth headers)
const publicApi = axios.create({
  baseURL: `${baseURL}/public`,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});
// AI chat API instance (NO auth headers)
const aiChatApi = axios.create({
  baseURL: `${baseURL}/chat`,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

export { api, publicApi, aiChatApi };
// -------------------- API FUNCTIONS --------------------

// login
export async function login(username, password) {
  const res = await api.post("accounts/login/", { username, password });
  const data = res.data;
  sessionStorage.setItem("token", data.access);
  return data;
}

// register
/**
 * Register a new user
 * @param {Object} userData - The registration data (username, email, password, role, etc.)
 * @returns {Promise} Axios response
 */
export const registerUser = async (userData) => {
  return await api.post('accounts/register/', userData);
};


// get current user
export async function me() {
  const res = await api.get("/accounts/me/");
  return res.data;
}

// offices
export async function myOffices() {
  const res = await api.get("/workspace/offices/");
  return res.data;
}

export async function createOffice(name, city) {
  const res = await api.post("/workspace/offices/", { name, city });
  return res.data;
}


