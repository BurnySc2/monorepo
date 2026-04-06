export interface Track {
    id: number
    name: string
}

export interface BestTimeEntry {
    date: string
    driver_name: string
    car_name: string
    driving_model: string
    track_name: string
    best_time: number
}

export type DateRange = "7d" | "30d" | "90d" | "1y" | "all"

export interface ChartDataPoint {
    date: Date
    driver_name: string
    car_name: string
    driving_model: string
    best_time: number
}

export interface DriverSeries {
    driver_name: string
    car_name: string
    driving_model: string
    color: string
    data: ChartDataPoint[]
}
