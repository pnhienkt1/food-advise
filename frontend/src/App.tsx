import { Link, Navigate, Route, Routes } from 'react-router-dom'
import { HistoryPage } from './pages/HistoryPage'
import { ProfilePage } from './pages/ProfilePage'
import { ResultPage } from './pages/ResultPage'
import { RecommendPage } from './pages/RecommendPage'
import { OcrPage } from './pages/OcrPage'
import { ScanPage } from './pages/ScanPage'

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
          <Link to="/scan" className="flex items-center gap-2">
            <span className="text-2xl">🥗</span>
            <span className="text-lg font-bold text-emerald-700">Food Advise</span>
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link to="/scan" className="text-slate-600 hover:text-emerald-600">
              Quét
            </Link>
            <Link to="/profile" className="text-slate-600 hover:text-emerald-600">
              Hồ sơ
            </Link>
            <Link to="/recommend" className="text-slate-600 hover:text-emerald-600">
              Gợi ý
            </Link>
            <Link to="/ocr" className="text-slate-600 hover:text-emerald-600">
              Thành phần
            </Link>
            <Link to="/history" className="text-slate-600 hover:text-emerald-600">
              Lịch sử
            </Link>
          </nav>
        </div>
      </header>
      <main>{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/scan" replace />} />
        <Route path="/scan" element={<ScanPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/result/:barcode" element={<ResultPage />} />
        <Route path="/recommend" element={<RecommendPage />} />
        <Route path="/ocr" element={<OcrPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </Layout>
  )
}
