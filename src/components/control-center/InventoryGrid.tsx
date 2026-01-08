import { useMemo } from "react";
import { addDays, format, startOfToday } from "date-fns";
import { cn } from "@/lib/utils";

// Mock Data Types
type RoomType = {
    id: string;
    name: string;
};

type DailyStats = {
    date: string; // YYYY-MM-DD
    inventory: number;
    rate: number;
    isSoldOut: boolean;
};

// Mock Room Types
const ROOM_TYPES: RoomType[] = [
    { id: "deluxe", name: "Deluxe King" },
    { id: "standard", name: "Standard Twin" },
    { id: "suite", name: "Executive Suite" },
    { id: "family", name: "Family Room" },
];

// Generate Mock Data for 30 days
const generateMockData = (startDate: Date, days: number) => {
    const data: Record<string, Record<string, DailyStats>> = {};

    ROOM_TYPES.forEach((room) => {
        data[room.id] = {};
        for (let i = 0; i < days; i++) {
            const date = addDays(startDate, i);
            const dateStr = format(date, "yyyy-MM-dd");
            // Random inventory between 0 and 10
            const inventory = Math.floor(Math.random() * 11);
            data[room.id][dateStr] = {
                date: dateStr,
                inventory,
                rate: 100 + Math.floor(Math.random() * 50), // Random rate 100-150
                isSoldOut: inventory === 0,
            };
        }
    });
    return data;
};

export function InventoryGrid() {
    const today = startOfToday();
    const days = 30;

    // Memoize dates and data
    const dateHeaders = useMemo(() => {
        return Array.from({ length: days }).map((_, i) => addDays(today, i));
    }, [today, days]);

    const gridData = useMemo(() => generateMockData(today, days), [today, days]);

    const getCellColor = (inventory: number, isSoldOut: boolean) => {
        if (isSoldOut || inventory === 0) return "bg-red-50 text-red-900"; // Sold out
        if (inventory <= 5) return "bg-amber-50 text-amber-900"; // Low inventory (Yellow)
        return "bg-emerald-50 text-emerald-900"; // High inventory (Green)
    };

    return (
        <div className="relative w-full overflow-x-auto">
            <div className="min-w-max">
                {/* Header Row */}
                <div className="flex border-b border-slate-200">
                    {/* Sticky Corner Logic could apply here if we use grid/table, for now simplified flex */}
                    <div className="w-48 sticky left-0 z-20 bg-slate-50 border-r border-slate-200 p-4 font-semibold text-slate-700 flex items-center shadow-[4px_0_8px_-4px_rgba(0,0,0,0.1)]">
                        Room Type
                    </div>
                    {/* Date Columns */}
                    {dateHeaders.map((date) => (
                        <div key={date.toString()} className="w-24 flex-shrink-0 border-r border-slate-100 p-2 text-center bg-slate-50 last:border-r-0">
                            <div className="text-xs font-medium text-slate-500 uppercase">{format(date, "EEE")}</div>
                            <div className="text-sm font-bold text-slate-900">{format(date, "d MMM")}</div>
                        </div>
                    ))}
                </div>

                {/* Rows */}
                <div className="divide-y divide-slate-100">
                    {ROOM_TYPES.map((room) => (
                        <div key={room.id} className="flex hover:bg-slate-50/50 transition-colors">
                            {/* Sticky Room Name */}
                            <div className="w-48 flex-shrink-0 sticky left-0 z-10 bg-white border-r border-slate-200 p-4 font-medium text-slate-900 flex items-center shadow-[4px_0_8px_-4px_rgba(0,0,0,0.1)]">
                                {room.name}
                            </div>

                            {/* Data Cells */}
                            {dateHeaders.map((date) => {
                                const dateStr = format(date, "yyyy-MM-dd");
                                const cellData = gridData[room.id][dateStr];
                                const colorClass = getCellColor(cellData.inventory, cellData.isSoldOut);

                                return (
                                    <div key={dateStr} className={cn("w-24 flex-shrink-0 border-r border-slate-100 p-2 flex flex-col justify-center items-center h-20 last:border-r-0 transition-colors cursor-pointer hover:brightness-95", colorClass)}>
                                        <div className={cn("text-lg font-bold leading-none", cellData.isSoldOut && "line-through opacity-50")}>
                                            {cellData.isSoldOut ? "SOLD" : cellData.inventory}
                                        </div>
                                        <div className="text-xs font-medium mt-1 opacity-80">
                                            ${cellData.rate}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
