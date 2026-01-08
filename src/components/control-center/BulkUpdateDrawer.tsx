import { useState } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter, SheetClose } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import type { DateRange } from "react-day-picker";

interface BulkUpdateDrawerProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function BulkUpdateDrawer({ open, onOpenChange }: BulkUpdateDrawerProps) {
    const [date, setDate] = useState<DateRange | undefined>({
        from: new Date(),
        to: new Date(),
    });
    const [roomType, setRoomType] = useState<string>("");
    const [rate, setRate] = useState<string>("");
    const [isOpen, setIsOpen] = useState(true);

    const handleUpdate = () => {
        // Logic to update inventory would go here
        console.log("Updating", { date, roomType, rate, isOpen });
        onOpenChange(false);
    };

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent className="w-full sm:w-[540px] overflow-y-auto">
                <SheetHeader>
                    <SheetTitle>Bulk Update</SheetTitle>
                    <SheetDescription>
                        Modify rates and availability for a specific date range.
                    </SheetDescription>
                </SheetHeader>

                <div className="grid gap-6 py-6 font-medium">
                    {/* Date Range Picker */}
                    <div className="grid gap-2">
                        <Label>Date Range</Label>
                        <Popover>
                            <PopoverTrigger asChild>
                                <Button
                                    id="date"
                                    variant={"outline"}
                                    className={cn(
                                        "w-full justify-start text-left font-normal",
                                        !date && "text-muted-foreground"
                                    )}
                                >
                                    <CalendarIcon className="mr-2 h-4 w-4" />
                                    {date?.from ? (
                                        date.to ? (
                                            <>
                                                {format(date.from, "LLL dd, y")} -{" "}
                                                {format(date.to, "LLL dd, y")}
                                            </>
                                        ) : (
                                            format(date.from, "LLL dd, y")
                                        )
                                    ) : (
                                        <span>Pick a date range</span>
                                    )}
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0" align="start">
                                <Calendar
                                    initialFocus
                                    mode="range"
                                    defaultMonth={date?.from}
                                    selected={date}
                                    onSelect={setDate}
                                    numberOfMonths={2}
                                />
                            </PopoverContent>
                        </Popover>
                    </div>

                    {/* Room Type Selector */}
                    <div className="grid gap-2">
                        <Label htmlFor="room-type">Room Type</Label>
                        <Select onValueChange={setRoomType} value={roomType}>
                            <SelectTrigger id="room-type">
                                <SelectValue placeholder="Select room type" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="deluxe">Deluxe King</SelectItem>
                                <SelectItem value="standard">Standard Twin</SelectItem>
                                <SelectItem value="suite">Executive Suite</SelectItem>
                                <SelectItem value="family">Family Room</SelectItem>
                                <SelectItem value="all">All Room Types</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Rate Input */}
                    <div className="grid gap-2">
                        <Label htmlFor="rate">New Rate (USD)</Label>
                        <Input
                            id="rate"
                            type="number"
                            placeholder="e.g. 150"
                            value={rate}
                            onChange={(e) => setRate(e.target.value)}
                        />
                    </div>

                    {/* Availability Toggle */}
                    <div className="flex items-center justify-between space-x-2 border rounded-lg p-4">
                        <div className="flex flex-col space-y-1">
                            <Label htmlFor="availability">Open for Booking</Label>
                            <span className="text-xs text-muted-foreground">
                                Turn off to stop selling on all channels.
                            </span>
                        </div>
                        <Switch id="availability" checked={isOpen} onCheckedChange={setIsOpen} />
                    </div>
                </div>

                <SheetFooter>
                    <SheetClose asChild>
                        <Button variant="outline">Cancel</Button>
                    </SheetClose>
                    <Button onClick={handleUpdate} type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white">Apply Changes</Button>
                </SheetFooter>
            </SheetContent>
        </Sheet>
    );
}
