import React, { useEffect, useMemo, useState } from 'react'
import { Routes, Route, Link, useNavigate, Navigate, useLocation } from 'react-router-dom'
import { api, setAuthToken } from './api'

function RegisterPage() {
  const nav = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const submit = async (e) => {
    e.preventDefault()
    await api.post('/auth/register', { name, email, password })
    alert('Registered! Now login.')
    nav('/login')
  }
  return (
    <div>
      <h2>Register (User)</h2>
      <form onSubmit={submit} style={{ display: 'grid', gap: 8, maxWidth: 320 }}>
        <input placeholder="Name" value={name} onChange={e => setName(e.target.value)} required />
        <input placeholder="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
        <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit">Create account</button>
      </form>
      <div style={{ marginTop: 8 }}><Link to="/login">Have an account? Login</Link></div>
    </div>
  )
}

function LoginPage({ onLogin }) {
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const submit = async (e) => {
    e.preventDefault()
    const res = await api.post('/auth/login', { email, password })
    const { token, user } = res.data
    setAuthToken(token)
    localStorage.setItem('authToken', token)
    localStorage.setItem('currentUser', JSON.stringify(user))
    onLogin(user)
    if (user.role === 'admin') nav('/admin')
    else nav('/user')
  }
  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={submit} style={{ display: 'grid', gap: 8, maxWidth: 320 }}>
        <input placeholder="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
        <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit">Login</button>
      </form>
      <div style={{ marginTop: 8 }}><Link to="/register">No account? Register</Link></div>
    </div>
  )
}

function AdminPage() {
  const [products, setProducts] = useState([])
  const [editing, setEditing] = useState(null)
  const [users, setUsers] = useState([])
  const [selectedUser, setSelectedUser] = useState('')
  const [orders, setOrders] = useState([])

  const loadProducts = async () => setProducts((await api.get('/products')).data)
  const loadUsers = async () => setUsers((await api.get('/users')).data)
  const loadOrdersFor = async (uid) => setOrders(uid ? (await api.get(`/orders?user_id=${uid}`)).data : [])

  useEffect(() => { loadProducts(); loadUsers() }, [])

  const [pn, setPn] = useState(''); const [pp, setPp] = useState(''); const [pc, setPc] = useState('USD'); const [ps, setPs] = useState('')
  const createProduct = async (e) => {
    e.preventDefault()
    await api.post('/products', { name: pn, price: parseFloat(pp), currency: pc, stock: parseInt(ps || 0) })
    setPn(''); setPp(''); setPc('USD'); setPs('')
    loadProducts()
  }
  const save = async (p) => { await api.put(`/products/${p.id}`, p); setEditing(null); loadProducts() }
  const remove = async (id) => { await api.delete(`/products/${id}`); loadProducts() }

  const idToName = useMemo(() => Object.fromEntries(products.map(p => [p.id, p.name])), [products])

  return (
    <div>
      <h2>Admin Dashboard</h2>

      <div style={{ display: 'grid', gap: 8, maxWidth: 360, padding: 12, border: '1px solid #ddd', borderRadius: 8 }}>
        <strong>Create Product</strong>
        <input placeholder="Name" value={pn} onChange={e => setPn(e.target.value)} />
        <input placeholder="Price" type="number" step="0.01" value={pp} onChange={e => setPp(e.target.value)} />
        <input placeholder="Currency" value={pc} onChange={e => setPc(e.target.value)} />
        <input placeholder="Stock" type="number" value={ps} onChange={e => setPs(e.target.value)} />
        <button onClick={createProduct}>Create</button>
      </div>

      <h3>Products</h3>
      <table border="1" cellPadding="6">
        <thead>
          <tr><th>Name</th><th>Price</th><th>Currency</th><th>Stock</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {products.map(p => (
            <tr key={p.id}>
              <td>{editing?.id === p.id ? <input value={editing.name} onChange={e => setEditing({ ...editing, name: e.target.value })} /> : p.name}</td>
              <td>{editing?.id === p.id ? <input type="number" step="0.01" value={editing.price} onChange={e => setEditing({ ...editing, price: parseFloat(e.target.value) })} /> : p.price}</td>
              <td>{editing?.id === p.id ? <input value={editing.currency} onChange={e => setEditing({ ...editing, currency: e.target.value })} /> : p.currency}</td>
              <td>{editing?.id === p.id ? <input type="number" value={editing.stock} onChange={e => setEditing({ ...editing, stock: parseInt(e.target.value) })} /> : p.stock}</td>
              <td>
                {editing?.id === p.id ? (
                  <>
                    <button onClick={() => save(editing)}>Save</button>
                    <button onClick={() => setEditing(null)}>Cancel</button>
                  </>
                ) : (
                  <>
                    <button onClick={() => setEditing(p)}>Edit</button>
                    <button onClick={() => remove(p.id)}>Delete</button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 style={{ marginTop: 24 }}>User Orders</h3>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
        <select
          value={selectedUser}
          onChange={e => {
            const uid = e.target.value
            setSelectedUser(uid)
            loadOrdersFor(uid)
          }}
        >
          <option value="">Select user</option>
          {users.map(u => <option key={u.id} value={u.id}>{u.name} ({u.email})</option>)}
        </select>
      </div>
      <table border="1" cellPadding="6">
        <thead>
          <tr><th>Product</th><th>Quantity</th><th>Status</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {orders.map(o => (
            <tr key={o.id}>
              <td>{idToName[o.product_id] || `#${o.product_id}`}</td>
              <td>{o.quantity}</td>
              <td>{o.status}</td>
              <td>
                <button
                  onClick={async () => {
                    if (!confirm('Delete this order?')) return
                    try {
                      await api.delete(`/orders/${o.id}`)
                      if (selectedUser) {
                        await loadOrdersFor(selectedUser)
                      } else {
                        setOrders(prev => prev.filter(x => x.id !== o.id))
                      }
                    } catch (err) {
                      const status = err?.response?.status
                      const msg = err?.response?.data?.error || err?.message || 'Unknown error'
                      alert(`Failed to delete (status ${status ?? 'n/a'}): ${msg}`)
                      console.error('DELETE /orders failed:', err?.response || err)
                    }
                  }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function UserPage() {
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])

  const loadProducts = async () => setProducts((await api.get('/products')).data)
  const loadOrders = async () => setOrders((await api.get('/orders')).data)

  useEffect(() => { loadProducts(); loadOrders() }, [])

  const [pid, setPid] = useState(''); const [qty, setQty] = useState(1)
  const createOrder = async (e) => {
    e.preventDefault()
    if (!pid) return
    await api.post('/orders', { product_id: parseInt(pid), quantity: parseInt(qty) })
    setPid(''); setQty(1)
    await loadOrders()
    await loadProducts()
  }

  const idToName = useMemo(() => Object.fromEntries(products.map(p => [p.id, p.name])), [products])

  return (
    <div>
      <h2>User Dashboard</h2>

      <h3>Create Order</h3>
      <form onSubmit={createOrder} style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <select value={pid} onChange={e => setPid(e.target.value)} required>
          <option value="">Select product</option>
          {products.map(p => (
            <option key={p.id} value={p.id}>
              {p.name} — {p.price} {p.currency}
            </option>
          ))}
        </select>
        <input type="number" min="1" value={qty} onChange={e => setQty(e.target.value)} />
        <button type="submit">Order</button>
      </form>

      <h3 style={{ marginTop: 16 }}>My Orders</h3>
      <table border="1" cellPadding="6">
        <thead>
          <tr><th>Product</th><th>Qty</th><th>Status</th></tr>
        </thead>
        <tbody>
          {orders.map(o => (
            <tr key={o.id}>
              <td>{idToName[o.product_id] || `#${o.product_id}`}</td>
              <td>{o.quantity}</td>
              <td>{o.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ProtectedRoute({ me, requireRole, children }) {
  if (!me) return <Navigate to="/login" replace />
  if (requireRole && me.role !== requireRole) return <Navigate to="/login" replace />
  return children
}

function Navbar({ me, onLogout }) {
  const loc = useLocation()
  const onAuthPage = loc.pathname === '/login' || loc.pathname === '/register' || loc.pathname === '/'

  if (!me && onAuthPage) {
    return (
      <nav style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Link to="/login">Login</Link>
        <Link to="/register">Register</Link>
      </nav>
    )
  }

  if (me) {
    return (
      <nav style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center' }}>
        <span><strong>Hello {me.role === 'admin' ? 'admin' : me.name}</strong></span>
        <button onClick={onLogout}>Logout</button>
      </nav>
    )
  }

  return (
    <nav style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
      <Link to="/login">Login</Link>
      <Link to="/register">Register</Link>
    </nav>
  )
}

function HomeRedirect({ me }) {
  if (me?.role === 'admin') return <Navigate to="/admin" replace />
  if (me) return <Navigate to="/user" replace />
  return <Navigate to="/login" replace />
}

export default function App() {
  const nav = useNavigate()
  const [me, setMe] = useState(() => {
    const saved = localStorage.getItem('currentUser')
    return saved ? JSON.parse(saved) : null
  })

  useEffect(() => {
    const token = localStorage.getItem('authToken')
    if (token) setAuthToken(token)
  }, [])

  const logout = () => {
    setAuthToken(null)
    localStorage.removeItem('authToken')
    localStorage.removeItem('currentUser')
    setMe(null)
    nav('/login')
  }

  return (
    <div style={{ padding: 20, fontFamily: 'sans-serif' }}>
      <Navbar me={me} onLogout={logout} />
      <Routes>
        <Route path="/" element={<HomeRedirect me={me} />} />
        <Route path="/login" element={<LoginPage onLogin={setMe} />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute me={me} requireRole="admin">
              <AdminPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/user"
          element={
            <ProtectedRoute me={me}>
              <UserPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  )
}
