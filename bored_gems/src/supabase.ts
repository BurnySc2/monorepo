import { createClient, type Session, type User } from "@supabase/supabase-js"

const supabaseUrl = "https://xplbweeaklyxixlugeju.supabase.co"
const supabaseAnonKey =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhwbGJ3ZWVha2x5eGl4bHVnZWp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDUwMzUwMTcsImV4cCI6MTk2MDYxMTAxN30.PPa4MEwdlaSQovk5lyKqIyxsxp7ujYqjlNGMsctho8k"

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
// TODO Make username primary key = unique
// 16:57 CENSORED: cant change to unique when editing, just creating column
export const supabaseUsernameTable = supabase.from("bored_gems_usernames")
export const supabaseLobbyTable = supabase.from("bored_gems_lobby")
export const supabasePlayerTable = supabase.from("bored_gems_players")

export const getSupabaseUserFromSession = async (): Promise<User | null> => {
    const session: Session | null = await supabase.auth.session()
    if (session) {
        let user: User | null = session.user
        if (user) {
            return user
        }
    }
    return null
}

export const getUsernameOfUser = async (user: User): Promise<string | null> => {
    if (!user.email) {
        return null
    }
    const response = await supabaseUsernameTable.select("username").eq("email", user.email).limit(1).single()
    return response.data.username || null
}
