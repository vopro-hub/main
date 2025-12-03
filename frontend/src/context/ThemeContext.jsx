import { createContext, useState, useEffect } from 'react'

export const ThemeContext = createContext()

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')

  useEffect(() => {
    // apply theme to <html>
    document.documentElement.setAttribute('data-theme', theme)

    // apply theme as class (for Tailwind dark mode)
    document.documentElement.classList.remove('light', 'dark')
    document.documentElement.classList.add(theme)

    // save preference
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(prev => (prev === 'light' ? 'dark' : 'light'))

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
