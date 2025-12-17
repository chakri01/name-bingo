import React, { useState, useEffect } from 'react'
  const hasPhoto = profileData?.photo
  const isBlurred = profileData?.blur
export default function Admin({ apiUrl }) {
  const [authenticated, setAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [gameStatus, setGameStatus] = useState(null)
  const [claims, setClaims] = useState([])
  const [selectedClaim, setSelectedClaim] = useState(null)
  const [qrData, setQrData] = useState(null)
  const [showQr, setShowQr] = useState(false)
  const [showNameReveal, setShowNameReveal] = useState(false)
  const [revealedName, setRevealedName] = useState(null)
  const [profileData, setProfileData] = useState(null)
  const [revealed, setRevealed] = useState(false)

  useEffect(() => {
    if (authenticated) {
      loadQrCode()
      const interval = setInterval(() => {
        loadGameStatus()
        loadClaims()
      }, 1000)
      return () => clearInterval(interval)
    }
}, [authenticated])
  const loadQrCode = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/admin/qr-code`)
      const data = await res.json()
      setQrData(data)
    } catch (err) {
      console.error('Failed to load QR code:', err)
    }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch(`${apiUrl}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      })
      if (res.ok) {
        setAuthenticated(true)
      } else {
        alert('Invalid password')
      }
    } catch (err) {
      alert('Login failed')
    }
  }

  const loadGameStatus = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/game-status`)
      const data = await res.json()
      setGameStatus(data)
    } catch (err) {
      console.error(err)
    }
  }

  const loadClaims = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/admin/claims`)
      const data = await res.json()
      setClaims(data)
    } catch (err) {
      console.error(err)
    }
  }

  const pickName = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/admin/pick-name`, { method: 'POST' })
      const data = await res.json()
      console.log('Picked name:', data.picked_name)
      
      // Fetch profile data
      const profileRes = await fetch(`${apiUrl}/api/profile/${encodeURIComponent(data.picked_name)}`)
      const profile = await profileRes.json()

      setRevealedName(data)
      setProfileData(profile)
      setRevealed(!profile?.blur) // Auto-reveal if not blurred
      setShowNameReveal(true)

    } catch (err) {
      alert('Pick failed')
    }
  }

  const verifyClaim = async (claimId, isValid) => {
    try {
      await fetch(`${apiUrl}/api/admin/verify-claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ claim_id: claimId, is_valid: isValid })
      })
      setSelectedClaim(null)
      loadClaims()
    } catch (err) {
      alert('Verification failed')
    }
  }

  const resetGame = async () => {
    if (!confirm('Reset entire game?')) return
    try {
      await fetch(`${apiUrl}/api/admin/reset-game`, { method: 'POST' })
      alert('Game reset')
      loadGameStatus()
    } catch (err) {
      alert('Reset failed')
    }
  }

  if (!authenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black flex items-center justify-center p-4">
        <form onSubmit={handleLogin} className="bg-white rounded-lg p-8 max-w-md w-full">
          <h1 className="text-2xl font-bold mb-4">Nambola Admin</h1>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-3 border rounded-lg mb-4"
          />
          <button className="w-full bg-black text-white py-3 rounded-lg font-semibold">
            Login
          </button>
        </form>
      </div>
    )
  }

  

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black text-white p-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Nambola Admin</h1>
          <button
            onClick={() => setShowQr(!showQr)}
            className="bg-purple-600 px-6 py-2 rounded-lg hover:bg-purple-700"
          >
            {showQr ? 'Hide QR' : 'Show QR Code'}
          </button>
        </div>

        {showQr && qrData && (
          <div className="bg-white rounded-lg p-6 mb-6 text-center">
            <h2 className="text-black text-xl font-bold mb-4">Player Join QR Code</h2>
            <img src={qrData.qr_code} alt="QR Code" className="mx-auto mb-4" style={{width: '300px'}} />
            <p className="text-black font-mono text-sm">{qrData.url}</p>
            <p className="text-gray-600 text-sm mt-2">Players scan this to join the game</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <button
            onClick={pickName}
            className="bg-blue-600 py-8 rounded-lg text-2xl font-bold hover:bg-blue-700"
          >
            PICK NAME
          </button>
          <button
            onClick={resetGame}
            className="bg-red-600 py-8 rounded-lg text-2xl font-bold hover:bg-red-700"
          >
            RESET GAME
          </button>
        </div>

        {claims.length > 0 && (
          <div className="bg-yellow-600 p-4 rounded-lg mb-6">
            <h2 className="text-xl font-bold mb-2">⚠️ Pending Claims: {claims.length}</h2>
            {claims.map(claim => (
              <div key={claim.claim_id} className="bg-white text-black p-4 rounded mb-2">
                <p className="font-bold">{claim.player_name}</p>
                <button
                  onClick={() => setSelectedClaim(claim)}
                  className="bg-blue-600 text-white px-4 py-2 rounded mt-2"
                >
                  Review
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Called Names</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {gameStatus?.picked_names.map((n, i) => (
              <div key={i} className="bg-green-600 p-3 rounded text-center">
                {n.name}
              </div>
            ))}
          </div>
        </div>

        {/* Name Reveal Modal */}
        {showNameReveal && revealedName && (
          <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 animate-fadeIn">
            <div className="bg-white rounded-2xl p-8 max-w-2xl w-full mx-4 animate-popIn">
              <div className="text-center">
                <div className="text-6xl mb-4">🎉</div>
                
                  {hasPhoto && (
                    <div className="mb-6">
                      <img
                        src={`${apiUrl}${encodeURI(profileData.photo)}`}
                        alt={revealedName.picked_name}
                        className={`w-96 h-auto mx-auto rounded-xl object-contain shadow-2xl ${
                          isBlurred && !revealed ? 'blur-2xl' : ''
                        }`}
                        style={{
                          transition: 'filter 0.5s ease'
                        }}
                      />
                      {isBlurred && !revealed && (
                        <button
                          onClick={() => setRevealed(true)}
                          className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                        >
                          Reveal Photo
                        </button>
                      )}
                    </div>
                  )}

                  <h2 className="text-5xl font-bold text-gray-800 mb-4">
                    {revealedName.picked_name}
                  </h2>

                  {profileData?.bio && (
                    <p className="text-xl text-gray-600 mb-6 italic">
                      "{profileData.bio}"
                    </p>
                  )}
                
                <div className="flex justify-center gap-8 text-gray-700">
                  <div>
                    <div className="text-3xl font-bold text-blue-600">#{revealedName.order}</div>
                    <div className="text-sm">Call Number</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-green-600">{revealedName.remaining}</div>
                    <div className="text-sm">Remaining</div>
                  </div>
                </div>
                
                <button
                  onClick={() => {
                    setShowNameReveal(false)
                    loadGameStatus()
                  }}
                  className="mt-6 bg-gray-800 text-white px-8 py-3 rounded-lg hover:bg-gray-900"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Claim Verification Modal */}
        {selectedClaim && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-40">
            <div className="bg-white text-black rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold mb-4">{selectedClaim.player_name}</h2>
              
              <div className="grid grid-cols-9 gap-1 mb-6">
                {selectedClaim.grid.map((row, ridx) =>
                  row.map((cell, cidx) => {
                    const isPicked = selectedClaim.picked_names.includes(cell)
                    return (
                      <div
                        key={`${ridx}-${cidx}`}
                        className={`aspect-square flex items-center justify-center text-xs font-semibold rounded border-2 ${
                          !cell ? 'bg-gray-200' :
                          isPicked ? 'bg-green-500 text-white' :
                          'bg-white border-gray-300'
                        }`}
                      >
                        {cell ? cell.split('_')[1] || cell : ''}
                      </div>
                    )
                  })
                )}
              </div>

              <div className="flex gap-4">
                <button
                  onClick={() => verifyClaim(selectedClaim.claim_id, true)}
                  className="flex-1 bg-green-600 text-white py-3 rounded-lg font-bold"
                >
                  ✓ VERIFY WIN
                </button>
                <button
                  onClick={() => verifyClaim(selectedClaim.claim_id, false)}
                  className="flex-1 bg-red-600 text-white py-3 rounded-lg font-bold"
                >
                  ✗ REJECT
                </button>
                <button
                  onClick={() => setSelectedClaim(null)}
                  className="px-6 bg-gray-400 text-white py-3 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
