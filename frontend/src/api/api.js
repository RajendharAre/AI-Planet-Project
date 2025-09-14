import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"
});

export const uploadDoc = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/docs/upload", fd, { headers: { "Content-Type": "multipart/form-data" }});
};

export const runWorkflow = (definition, query, custom_prompt=null) => {
  return api.post("/workflow/run", {definition, query, custom_prompt});
};
