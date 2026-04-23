import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Home    from './pages/Home'
import Results from './pages/Results'
import Compare from './pages/Compare'

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main>
        <Routes>
          <Route path="/"        element={<Home />} />
          <Route path="/results" element={<Results />} />
          <Route path="/compare" element={<Compare />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
