import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://ezykqdzqholcporflgmq.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseAnonKey) {
    console.warn(' VITE_SUPABASE_ANON_KEY is not set. Realtime features will not work.')
    console.warn(' Get your key from: https://supabase.com/dashboard/project/ezykqdzqholcporflgmq/settings/api')
}

export const supabase = supabaseAnonKey ? createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
        persistSession: false, // We use JWT auth from backend
        autoRefreshToken: false
    },
    realtime: {
        params: {
            eventsPerSecond: 10
        }
    }
}) : null

// Test connection only if client was created
if (supabase) {
    supabase.channel('test').subscribe((status) => {
        if (status === 'SUBSCRIBED') {
            console.log(' Supabase Realtime connected')
        } else if (status === 'CHANNEL_ERROR') {
            console.error(' Supabase Realtime connection failed - check your anon key')
        }
    })
}
