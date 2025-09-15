import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"
});

export const uploadDoc = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/api/v1/documents/upload-public", fd, { headers: { "Content-Type": "multipart/form-data" }});
};

export const runWorkflow = (definition, query, custom_prompt=null) => {
  return api.post("/api/v1/workflows/run-public", {definition, query, custom_prompt});
};
