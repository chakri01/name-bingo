import React, { useState, useEffect } from 'react'

export default function Play({ apiUrl, ticketId }) {
  const [ticket, setTicket] = useState(null)
  const [gameStatus, setGameStatus] = useState(null)
  const [marked, setMarked] = useState({})
  const [claiming, setClaiming] = useState(false)

  useEffect(() => {
    loadTicket()
    const saved = localStorage.getItem(`marked_${ticketId}`)
    if (saved) setMarked(JSON.parse(saved))
  }, [ticketId])

  useEffect(() => {
    const interval = setInterval(() => {
      loadGameStatus()
    }, 2000 + Math.random() * 2000)
    return () => clearInterval(interval)
  }, [])

  const loadTicket = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/ticket/${ticketId}`)
      const data = await res.json()
      setTicket(data)
    } catch (err) {
      console.error('Load ticket error:', err)
    }
  }

  const loadGameStatus = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/game-status`)
      const data = await res.json()
      console.log('Game Status Response:', data) // DEBUG LOG
      setGameStatus(data)
    } catch (err) {
      console.error('Load game status error:', err)
    }
  }

  const toggleMark = (row, col) => {
    const key = `${row}-${col}`
    const newMarked = { ...marked, [key]: !marked[key] }
    setMarked(newMarked)
    localStorage.setItem(`marked_${ticketId}`, JSON.stringify(newMarked))
  }

  const handleClaim = async () => {
    setClaiming(true)
    try {
      const res = await fetch(`${apiUrl}/api/claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket_id: ticketId })
      })
      const data = await res.json()
      if (data.success) {
        alert('Claim submitted! Waiting for verification...')
      } else {
        alert(data.message)
      }
    } catch (err) {
      alert('Claim failed')
    } finally {
      setClaiming(false)
    }
  }

  if (!ticket) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    )
  }

  if (ticket.status === 'winner') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 to-emerald-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-2xl p-8 text-center">
          <h1 className="text-4xl font-bold text-green-600 mb-4">🎉 WINNER! 🎉</h1>
          <p className="text-xl">{ticket.player_name}</p>
        </div>
      </div>
    )
  }

  // DEBUG INFO
  const buttonDisabled = claiming || ticket.status === 'claimed' || gameStatus?.is_locked
  console.log('Button disabled?', buttonDisabled, {
    claiming,
    ticketStatus: ticket.status,
    isLocked: gameStatus?.is_locked
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 to-pink-900 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-2xl p-6">
          <h2 className="text-2xl font-bold text-center mb-4">{ticket.player_name}</h2>
          
          <div className="grid grid-cols-9 gap-1 mb-6">
            {ticket.grid.map((row, ridx) =>
              row.map((cell, cidx) => {
                const key = `${ridx}-${cidx}`
                const isMarked = marked[key]
                
                return (
                  <div
                    key={key}
                    onClick={() => cell && toggleMark(ridx, cidx)}
                    className={`aspect-square flex items-center justify-center text-xs font-semibold rounded cursor-pointer border-2 ${
                      !cell ? 'bg-gray-200' :
                      isMarked ? 'bg-green-500 text-white border-green-700' :
                      'bg-white border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {cell ? cell.split('_')[1] || cell : ''}
                  </div>
                )
              })
            )}
          </div>

          <button
            onClick={handleClaim}
            disabled={buttonDisabled}
            className="w-full bg-red-600 text-white py-4 rounded-lg font-bold text-xl hover:bg-red-700 disabled:bg-gray-400"
          >
            {ticket.status === 'claimed' ? 'Waiting for Verification...' :
             gameStatus?.is_locked ? 'Claim in Progress...' :
             claiming ? 'Submitting...' : 'CLAIM WIN'}
          </button>

          {/* DEBUG INFO */}
          <div className="mt-4 p-3 bg-gray-100 rounded text-xs">
            <p><strong>Debug Info:</strong></p>
            <p>Ticket Status: {ticket.status}</p>
            <p>Game Locked: {String(gameStatus?.is_locked)}</p>
            <p>Called: {gameStatus?.picked_names?.length || 0}</p>
          </div>
        </div>
      </div>
    </div>
  )
}