export interface MediaViewerState {
    is_loading: boolean
    error_message: string | null
}

export const MEDIA_LOAD_ERROR_MESSAGE = "This media could not be loaded or decoded. It may be unavailable or corrupted."

export function initial_media_viewer_state(): MediaViewerState {
    return { is_loading: true, error_message: null }
}

export function media_load_started(): MediaViewerState {
    return { is_loading: true, error_message: null }
}

export function media_loaded(): MediaViewerState {
    return { is_loading: false, error_message: null }
}

export function media_load_failed(): MediaViewerState {
    return { is_loading: false, error_message: MEDIA_LOAD_ERROR_MESSAGE }
}
