import React, { useEffect, useState } from 'react'
import Register from './Register'
import Play from './Play'
import Admin from './Admin'

const API_URL = import.meta.env.VITE_API_URL
export default function App() {
  const [view, setView] = useState('register')
  const [ticketId, setTicketId] = useState(null)

  useEffect(() => {
    const path = window.location.pathname
    const params = new URLSearchParams(window.location.search)
    
    if (path === '/admin') {
      setView('admin')
    } else if (path === '/play') {
      const tid = params.get('ticketId') || localStorage.getItem('ticketId')
      if (tid) {
        setTicketId(tid)
        setView('play')
      }
    } else {
      const stored = localStorage.getItem('ticketId')
      if (stored) {
        setTicketId(stored)
        setView('play')
      }
    }
  }, [])

  const handleRegistered = (tid) => {
    localStorage.setItem('ticketId', tid)
    setTicketId(tid)
    setView('play')
    window.history.pushState({}, '', `/play?ticketId=${tid}`)
  }

  if (view === 'admin') {
    return <Admin apiUrl={API_URL} />
  }

  if (view === 'play' && ticketId) {
    return <Play apiUrl={API_URL} ticketId={ticketId} />
  }

  return <Register apiUrl={API_URL} onRegistered={handleRegistered} />
}