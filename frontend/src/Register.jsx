import React, { useState, useEffect } from 'react'

export default function Register({ apiUrl, onRegistered }) {
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [allNames, setAllNames] = useState([])
  const [filteredNames, setFilteredNames] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)

  // Fetch all available names on mount
  useEffect(() => {
    const fetchNames = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/names`)
        if (res.ok) {
          const data = await res.json()
          setAllNames(data.names || [])
        }
      } catch (err) {
        console.error('Failed to fetch names:', err)
      }
    }
    fetchNames()
  }, [apiUrl])

  // Filter names as user types
  useEffect(() => {
    if (name.trim().length > 0) {
      const searchTerm = name.toLowerCase()
      const matches = allNames.filter(n => 
        n.toLowerCase().includes(searchTerm)
      )
      setFilteredNames(matches)
      setShowDropdown(matches.length > 0)
    } else {
      setFilteredNames([])
      setShowDropdown(false)
    }
  }, [name, allNames])

  const handleNameSelect = (selectedName) => {
    setName(selectedName)
    setShowDropdown(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return

    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${apiUrl}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_name: name })
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Registration failed')
      }

      const data = await res.json()
      onRegistered(data.ticket_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-center mb-6 text-gray-800">Nambola</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Enter your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onFocus={() => name.trim() && setShowDropdown(filteredNames.length > 0)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              autoComplete="off"
            />
            {showDropdown && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {filteredNames.map((n, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleNameSelect(n)}
                    className="px-4 py-2 hover:bg-blue-100 cursor-pointer"
                  >
                    {n}
                  </div>
                ))}
              </div>
            )}
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Joining...' : 'Join Game'}
          </button>
        </form>
      </div>
    </div>
  )
}