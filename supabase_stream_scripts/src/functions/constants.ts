import { createClient } from '@supabase/supabase-js'

// Supabase
export const supabase = createClient(
  "https://xplbweeaklyxixlugeju.supabase.co",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhwbGJ3ZWVha2x5eGl4bHVnZWp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDUwMzUwMTcsImV4cCI6MTk2MDYxMTAxN30.PPa4MEwdlaSQovk5lyKqIyxsxp7ujYqjlNGMsctho8k",
)