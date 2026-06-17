import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// Handle redirect from 404.html — restores the original path
// so refreshing /dashboard works on static hosts without server-side routing
(function () {
  const redirect = sessionStorage.getItem('redirect');
  if (redirect && redirect !== '/') {
    sessionStorage.removeItem('redirect');
    window.history.replaceState(null, '', redirect);
  }
})();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
