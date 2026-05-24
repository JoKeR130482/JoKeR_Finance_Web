import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

export default function Login() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const response = await authApi.login(email, password)
      const { access_token, refresh_token } = response.data
      
      const userRes = await authApi.getMe()
      setAuth(access_token, refresh_token, userRes.data)
      
      toast.success('Вход выполнен успешно!')
      navigate('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-600">JoKeR_Finance</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">Учёт личных финансов</p>
        </div>
        
        <div className="card">
          <h2 className="text-2xl font-bold mb-6 text-center">Вход</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Пароль</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>
          
          <p className="mt-4 text-center text-sm">
            Нет аккаунта?{' '}
            <Link to="/register" className="text-primary-600 hover:underline">
              Зарегистрироваться
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
