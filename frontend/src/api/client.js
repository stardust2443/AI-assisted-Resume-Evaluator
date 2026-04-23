import axios from 'axios'

const api = axios.create({ baseURL: '' }) // proxied via vite.config.js

/** Evaluate a single candidate */
export async function evaluateSingle(resumeFile, jdFile, jdText) {
  const form = new FormData()
  form.append('resume', resumeFile)
  if (jdFile)  form.append('job_description', jdFile)
  if (jdText)  form.append('jd_text', jdText)

  const { data } = await api.post('/evaluate', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/** Compare multiple candidates against one JD */
export async function compareMultiple(resumeFiles, jdFile, jdText) {
  const form = new FormData()
  resumeFiles.forEach(f => form.append('resumes', f))
  if (jdFile) form.append('job_description', jdFile)
  if (jdText) form.append('jd_text', jdText)

  const { data } = await api.post('/compare', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
