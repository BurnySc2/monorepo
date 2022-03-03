import { supabase } from "./constants"

type ITodoItem = {
    id: number
    todo_text: string
    created_at: string
    done_at?: string
}

export default {
    todos: {
        all: async () => {
            const response = await supabase.from("todos").select("*").order("id")
            if (response.status === 200) {
                return response.data as ITodoItem[]
            }
            return []
        },
    },
}
