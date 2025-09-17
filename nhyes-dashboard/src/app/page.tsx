"use client";

import React, { useState } from "react";
import Image from "next/image";
import { DateNavigator } from "@/components/date-navigator";
import { CapacityVisualization } from "@/components/capacity-visualization";
import { NetworkVisualization } from "@/components/network-visualization";
import { Calendar, Activity, BarChart3, Users, TrendingUp, AlertCircle } from "lucide-react";

export default function Dashboard() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [safetyMargin, setSafetyMargin] = useState(8.5);

  // Debug safety margin changes
  React.useEffect(() => {
    console.log('Safety margin updated to:', safetyMargin);
  }, [safetyMargin]);

  return (
    <div className="h-screen bg-nhs-pale-grey flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-white border-b border-nhs-grey-3 flex-shrink-0 z-10">
        <div className="px-4 py-2">
          <div className="flex items-center gap-3">
            <Image
              src="/nhyes.svg"
              alt="NHyeS Logo"
              width={100}
              height={50}
              priority
              className="h-10 w-auto"
            />
            <h1 className="text-2xl font-semibold text-nhs-text-colour">
              DNA Management Dashboard
            </h1>
          </div>
        </div>
      </header>

      {/* 3-Column Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Navigation & Calendar */}
        <aside className="w-[280px] bg-white border-r border-nhs-grey-3 flex flex-col overflow-y-auto">
          {/* Navigation Menu */}
          <nav className="border-b border-nhs-grey-3">
            <div className="p-4">
              <h2 className="text-xs font-semibold uppercase text-nhs-secondary-text-colour mb-3">Navigation</h2>
              <ul className="space-y-1">
                <li>
                  <button className="w-full flex items-center gap-3 px-3 py-2 rounded-md bg-nhs-blue text-white hover:bg-nhs-dark-blue transition-colors">
                    <Activity className="w-5 h-5" />
                    <span className="font-medium">Capacity Analysis</span>
                  </button>
                </li>
                <li>
                  <button className="w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-nhs-grey-5 text-nhs-text-colour transition-colors">
                    <BarChart3 className="w-5 h-5" />
                    <span className="font-medium">Network View</span>
                  </button>
                </li>
                <li>
                  <button className="w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-nhs-grey-5 text-nhs-text-colour transition-colors">
                    <Users className="w-5 h-5" />
                    <span className="font-medium">Patient Flow</span>
                  </button>
                </li>
                <li>
                  <button className="w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-nhs-grey-5 text-nhs-text-colour transition-colors">
                    <TrendingUp className="w-5 h-5" />
                    <span className="font-medium">Trends</span>
                  </button>
                </li>
              </ul>
            </div>
          </nav>

          {/* Compact Calendar */}
          <div className="flex-1 border-b border-nhs-grey-3">
            <div className="p-4 pb-2">
              <h2 className="flex items-center gap-2 text-xs font-semibold uppercase text-nhs-secondary-text-colour mb-3">
                <Calendar className="w-4 h-4" />
                Date Selection
              </h2>
            </div>
            <div className="px-2">
              <DateNavigator
                selectedDate={selectedDate}
                onDateSelect={setSelectedDate}
              />
            </div>
          </div>

          {/* Quick Stats */}
          <div className="p-4 border-b border-nhs-grey-3">
            <h2 className="text-xs font-semibold uppercase text-nhs-secondary-text-colour mb-3">Today's Stats</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-nhs-secondary-text-colour">DNA Rate</span>
                <span className="font-semibold text-nhs-red">12.5%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-nhs-secondary-text-colour">Appointments</span>
                <span className="font-semibold text-nhs-text-colour">487</span>
              </div>
              <div className="flex justify-between">
                <span className="text-nhs-secondary-text-colour">Capacity</span>
                <span className="font-semibold text-nhs-green">78%</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content - Scrollable Feed */}
        <main className="flex-1 overflow-x-auto overflow-y-auto bg-nhs-grey-5">
          <div className="min-w-[800px] p-6">
            {/* Capacity Analysis Card */}
            <div className="bg-white rounded-lg border border-nhs-grey-3 mb-6">
              <div className="border-b border-nhs-grey-3 px-6 py-4">
                <h2 className="text-xl font-semibold text-nhs-text-colour">Capacity Analysis</h2>
                <p className="text-sm text-nhs-secondary-text-colour mt-1">
                  {selectedDate.toLocaleDateString('en-GB', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
              <div className="p-6 min-h-[500px]">
                <CapacityVisualization
                  selectedDate={selectedDate}
                  safetyMargin={safetyMargin}
                  onSafetyMarginChange={setSafetyMargin}
                />
              </div>
            </div>

            {/* Network Visualization Card */}
            <div className="bg-white rounded-lg border border-nhs-grey-3 mb-6">
              <div className="border-b border-nhs-grey-3 px-6 py-4">
                <h2 className="text-xl font-semibold text-nhs-text-colour">Network Analysis</h2>
                <p className="text-sm text-nhs-secondary-text-colour mt-1">
                  Patient flow and department connections
                </p>
              </div>
              <div className="p-6 h-[600px]">
                <NetworkVisualization className="h-full" />
              </div>
            </div>

            {/* Additional metrics cards can be added here */}
          </div>
        </main>

        {/* Right Sidebar - Alerts & Info */}
        <aside className="w-[320px] bg-white border-l border-nhs-grey-3 overflow-y-auto">
          {/* Alerts Section */}
          <div className="border-b border-nhs-grey-3 p-4">
            <h2 className="flex items-center gap-2 text-xs font-semibold uppercase text-nhs-secondary-text-colour mb-3">
              <AlertCircle className="w-4 h-4" />
              Active Alerts
            </h2>
            <div className="space-y-3">
              <div className="p-3 bg-nhs-warm-yellow bg-opacity-10 border border-nhs-warm-yellow rounded-md">
                <p className="text-sm font-medium text-nhs-text-colour">High DNA Rate</p>
                <p className="text-xs text-nhs-secondary-text-colour mt-1">
                  Cardiology dept showing 18% DNA rate
                </p>
              </div>
              <div className="p-3 bg-nhs-red bg-opacity-10 border border-nhs-red rounded-md">
                <p className="text-sm font-medium text-nhs-text-colour">Capacity Warning</p>
                <p className="text-xs text-nhs-secondary-text-colour mt-1">
                  A&E approaching 95% capacity
                </p>
              </div>
            </div>
          </div>

          {/* Network Legend */}
          <div className="p-4">
            <h2 className="text-xs font-semibold uppercase text-nhs-secondary-text-colour mb-3">Network Legend</h2>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-nhs-red"></div>
                <span className="text-sm text-nhs-text-colour">High Risk</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-nhs-orange"></div>
                <span className="text-sm text-nhs-text-colour">Medium Risk</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-nhs-green"></div>
                <span className="text-sm text-nhs-text-colour">Low Risk</span>
              </div>
            </div>

            <h3 className="text-xs font-semibold uppercase text-nhs-secondary-text-colour mt-6 mb-3">Node Types</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-nhs-grey-2"></div>
                <span className="text-sm text-nhs-text-colour">Patients (small)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-nhs-blue"></div>
                <span className="text-sm text-nhs-text-colour">Sites (large)</span>
              </div>
            </div>

            <h3 className="text-xs font-semibold uppercase text-nhs-secondary-text-colour mt-6 mb-3">Statistics</h3>
            <div className="space-y-1 text-sm text-nhs-secondary-text-colour">
              <div className="flex justify-between">
                <span>Nodes:</span>
                <span className="font-medium">4,033</span>
              </div>
              <div className="flex justify-between">
                <span>Links:</span>
                <span className="font-medium">3,892</span>
              </div>
              <div className="flex justify-between">
                <span>Communities:</span>
                <span className="font-medium">44</span>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="border-t border-nhs-grey-3 p-4">
            <h2 className="text-xs font-semibold uppercase text-nhs-secondary-text-colour mb-3">Recent Activity</h2>
            <div className="space-y-3">
              <div className="text-sm">
                <p className="text-nhs-text-colour">Capacity threshold updated</p>
                <p className="text-xs text-nhs-secondary-text-colour">2 minutes ago</p>
              </div>
              <div className="text-sm">
                <p className="text-nhs-text-colour">New DNA pattern detected</p>
                <p className="text-xs text-nhs-secondary-text-colour">15 minutes ago</p>
              </div>
              <div className="text-sm">
                <p className="text-nhs-text-colour">Weekly report generated</p>
                <p className="text-xs text-nhs-secondary-text-colour">1 hour ago</p>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
