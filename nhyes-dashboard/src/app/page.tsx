"use client";

import { useState } from "react";
import Image from "next/image";
import { DateNavigator } from "@/components/date-navigator";
import { CapacityVisualization } from "@/components/capacity-visualization";
import { NetworkVisualization } from "@/components/network-visualization";

export default function Dashboard() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [safetyMargin, setSafetyMargin] = useState(8.5);

  return (
    <div className="h-screen bg-nhs-light-grey flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-white border-b border-nhs-mid-grey flex-shrink-0">
        <div className="px-6 py-3">
          <div className="flex items-center gap-3">
            <Image
              src="/nhyes.svg"
              alt="NHyeS Logo"
              width={120}
              height={60}
              priority
              className="h-12 w-auto"
            />
            <h1 className="text-page-title text-nhs-black">
              Capacity Management Dashboard
            </h1>
          </div>
        </div>
      </header>

      {/* Main Dashboard Layout */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Top Half - Calendar and Capacity Analysis */}
        <div className="h-1/2 flex min-h-0">
          {/* Left Pane - Date Navigator (35% width) */}
          <div className="w-[35%] bg-white border-r border-nhs-mid-grey min-h-0">
            <DateNavigator
              selectedDate={selectedDate}
              onDateSelect={setSelectedDate}
            />
          </div>

          {/* Right Pane - Capacity Visualization (65% width) */}
          <div className="w-[65%] bg-white min-h-0">
            <CapacityVisualization
              selectedDate={selectedDate}
              safetyMargin={safetyMargin}
              onSafetyMarginChange={setSafetyMargin}
            />
          </div>
        </div>

        {/* Clean Divider */}
        <div className="border-t border-nhs-mid-grey flex-shrink-0"></div>

        {/* Bottom Half - Network Visualization */}
        <div className="h-1/2 bg-white min-h-0">
          <NetworkVisualization className="h-full" />
        </div>
      </div>
    </div>
  );
}
