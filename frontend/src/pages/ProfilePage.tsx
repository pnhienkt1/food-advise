import { Link } from 'react-router-dom'
import { ProfilePicker } from '../components/ProfilePicker'
import { Disclaimer } from '../components/ui'
import { useProfile } from '../hooks/useProfile'

export function ProfilePage() {
  const { profile, setProfile } = useProfile()

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4">
      <ProfilePicker profile={profile} onChange={setProfile} />
      <Disclaimer />
      <Link
        to="/scan"
        className="block rounded-xl bg-emerald-600 py-3 text-center font-medium text-white hover:bg-emerald-700"
      >
        Tiếp tục quét sản phẩm
      </Link>
    </div>
  )
}
