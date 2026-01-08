import { InventoryGrid } from "@/components/control-center/InventoryGrid";
import { ChannelHealthWidget } from "@/components/control-center/ChannelHealthWidget";
import { Button } from "@/components/ui/button";
import { BulkUpdateDrawer } from "@/components/control-center/BulkUpdateDrawer";
import { useState } from "react";

export default function ControlCenterPage() {
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);

    return (
        <div className="min-h-screen bg-slate-50 p-4 md:p-8 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">Control Center</h1>
                    <p className="text-slate-500 mt-1">Manage inventory, rates, and channels.</p>
                </div>
                <div className="flex gap-3">
                    {/* Open Drawer Button */}
                    <Button onClick={() => setIsDrawerOpen(true)}>Bulk Update</Button>
                </div>
            </div>

            {/* Channel Health Widget */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <ChannelHealthWidget />
            </div>

            {/* Inventory Grid */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="p-4 border-b border-slate-200">
                    <h2 className="text-lg font-semibold text-slate-900">Availability & Rates</h2>
                </div>
                <InventoryGrid />
            </div>

            <BulkUpdateDrawer open={isDrawerOpen} onOpenChange={setIsDrawerOpen} />
        </div>
    );
}
