import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, RefreshCw, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

type ChannelStatus = {
    id: string;
    name: string;
    status: "online" | "error";
    lastSync: string;
};

const CHANNELS: ChannelStatus[] = [
    { id: "booking", name: "Booking.com", status: "online", lastSync: "2 mins ago" },
    { id: "airbnb", name: "Airbnb", status: "online", lastSync: "5 mins ago" },
    { id: "expedia", name: "Expedia", status: "error", lastSync: "Failed 1h ago" },
    { id: "agoda", name: "Agoda", status: "online", lastSync: "10 mins ago" },
];

export function ChannelHealthWidget() {
    return (
        <Card className="col-span-1 md:col-span-3 border-slate-200 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="flex justify-between items-center text-lg font-medium">
                    <div className="flex items-center gap-2">
                        <Layers className="h-5 w-5 text-indigo-600" />
                        Channel Health
                    </div>
                    <Button variant="ghost" size="sm" className="text-slate-500 hover:text-indigo-600">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Refresh All
                    </Button>
                </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {CHANNELS.map((channel) => (
                    <div
                        key={channel.id}
                        className={cn(
                            "flex flex-col p-4 rounded-lg border transition-all hover:shadow-md",
                            channel.status === "error"
                                ? "bg-red-50 border-red-100"
                                : "bg-white border-slate-200"
                        )}
                    >
                        <div className="flex justify-between items-start mb-2">
                            <span className="font-semibold text-slate-900">{channel.name}</span>
                            {channel.status === "online" ? (
                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                            ) : (
                                <AlertCircle className="h-5 w-5 text-red-500" />
                            )}
                        </div>

                        <div className="text-sm text-slate-500 mt-1">
                            {channel.status === "online" ? (
                                <span className="text-emerald-700 flex items-center gap-1.5">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                    Synced {channel.lastSync}
                                </span>
                            ) : (
                                <div className="flex flex-col gap-2">
                                    <span className="text-red-700 flex items-center gap-1.5 text-xs font-medium">
                                        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                                        Auth Failed
                                    </span>
                                    <Button size="sm" variant="destructive" className="h-7 text-xs w-full">
                                        Reconnect
                                    </Button>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}
