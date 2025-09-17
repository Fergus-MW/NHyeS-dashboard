"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";

interface CapacityVisualizationProps {
  selectedDate: Date;
  safetyMargin: number;
  onSafetyMarginChange: (value: number) => void;
}

interface TooltipData {
  label: string;
  value: number;
  x: number;
  y: number;
}

// Mock data generation based on date
const generateCapacityData = (date: Date, safetyMargin: number) => {
  // Use date as seed for consistent data
  const seed = date.getTime() / (1000 * 60 * 60 * 24);
  const random = (offset: number = 0) => (Math.sin(seed + offset) + 1) / 2;
  
  const totalCapacity = 500;
  const baseAttendance = Math.floor(totalCapacity * (0.6 + random(1) * 0.25)); // 60-85% base
  
  // Booking Strategy (Bar 1)
  const projectedAttendance = baseAttendance + Math.floor(random(2) * 20 - 10); // ±10 variation
  const safetyMarginAmount = Math.floor(totalCapacity * (safetyMargin / 100));
  const strategicOverbooking = totalCapacity - projectedAttendance - safetyMarginAmount;
  
  // Actual Outcome (Bar 2) - should be close to projected + strategic overbooking ± 15
  const targetAttendance = projectedAttendance + Math.max(0, strategicOverbooking);
  const randomOffset = Math.floor((random(3) - 0.5) * 30); // ±15 range (random(3) gives 0-1, so -0.5 to 0.5, then * 30 = ±15)
  const actualAttendance = Math.max(0, targetAttendance + randomOffset); // Remove capacity limit to allow over-capacity
  const wastedCapacity = Math.max(0, totalCapacity - actualAttendance); // Wasted capacity can't be negative
  
  return {
    totalCapacity,
    bookingStrategy: {
      projectedAttendance,
      strategicOverbooking: Math.max(0, strategicOverbooking),
      safetyMargin: safetyMarginAmount,
    },
    actualOutcome: {
      actualAttendance,
      wastedCapacity,
    },
  };
};

export function CapacityVisualization({ 
  selectedDate, 
  safetyMargin, 
  onSafetyMarginChange 
}: CapacityVisualizationProps) {
  const [data, setData] = useState(generateCapacityData(selectedDate, safetyMargin));
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);

  // Update data when date or safety margin changes
  useEffect(() => {
    setData(generateCapacityData(selectedDate, safetyMargin));
  }, [selectedDate, safetyMargin]);

  const maxHeight = 400
  ; // Chart height in pixels
  
  // Calculate percentages for visualization
  const getPercentage = (value: number) => (value / data.totalCapacity) * 100;
  const getPixelHeight = (value: number) => (value / data.totalCapacity) * maxHeight;
  
  const handleSliderChange = (values: number[]) => {
    onSafetyMarginChange(values[0]);
  };

  const showTooltip = (label: string, value: number, event: React.MouseEvent) => {
    setTooltip({
      label,
      value,
      x: event.clientX,
      y: event.clientY,
    });
  };

  const hideTooltip = () => {
    setTooltip(null);
  };

  // Check if actual attendance exceeds capacity
  const isOverCapacity = data.actualOutcome.actualAttendance > data.totalCapacity;

  return (
    <div className="p-4 h-full flex overflow-hidden min-h-0">
      {/* Left Column - Text and Controls */}
      <div className="w-1/2 flex flex-col justify-center pr-6">
        <div className="mb-6">
          <h2 className="text-section-title text-nhs-black mb-2">
            Capacity Analysis
          </h2>
          <p className="text-body text-nhs-black">
            {selectedDate.toLocaleDateString('en-GB', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>

        {/* Safety Margin Slider */}
        <div className="max-w-md">
          <div className="flex items-center justify-between mb-3">
            <label className="text-body font-medium text-nhs-black">
              Adjust Safety Margin
            </label>
            <span className="text-body-small font-medium text-nhs-blue">
              {safetyMargin.toFixed(1)}%
            </span>
          </div>
          
          <Slider
            value={[safetyMargin]}
            onValueChange={handleSliderChange}
            min={0}
            max={30}
            step={0.5}
            className="w-full"
          />
          
          <div className="flex justify-between text-body-small text-nhs-mid-grey mt-1">
            <span>0%</span>
            <span>30%</span>
          </div>
        </div>
      </div>

      {/* Right Column - Charts */}
      <div className="w-1/2 flex items-center justify-center gap-8">
        {/* Y-Axis */}
        <div className="h-[250px] flex flex-col justify-between text-body-small text-nhs-mid-grey pr-2">
          <span>{data.totalCapacity}</span>
          <span>{Math.floor(data.totalCapacity * 0.5)}</span>
          <span>0</span>
        </div>

        {/* Bar 1: Booking Strategy */}
        <div className="flex flex-col items-center gap-4">
          <div className="relative bg-nhs-light-grey rounded border border-nhs-mid-grey overflow-hidden" 
               style={{ width: 80, height: maxHeight }}>
            
            {/* Projected Attendance (Bottom) */}
            <div
              className="absolute bottom-0 w-full bg-data-projected-blue"
              style={{ 
                height: getPixelHeight(data.bookingStrategy.projectedAttendance),
                zIndex: 1,
              }}
              onMouseEnter={(e) => showTooltip("Projected Attendance", data.bookingStrategy.projectedAttendance, e)}
              onMouseLeave={hideTooltip}
              onMouseMove={(e) => showTooltip("Projected Attendance", data.bookingStrategy.projectedAttendance, e)}
            />
            
            {/* Strategic Overbooking (Middle) */}
            <div
              className="absolute w-full bg-data-strategic-blue border-t border-blue-400 border-b border-blue-400"
              style={{ 
                bottom: getPixelHeight(data.bookingStrategy.projectedAttendance),
                height: getPixelHeight(data.bookingStrategy.strategicOverbooking),
                zIndex: 2,
              }}
              onMouseEnter={(e) => showTooltip("Strategic Overbooking", data.bookingStrategy.strategicOverbooking, e)}
              onMouseLeave={hideTooltip}
              onMouseMove={(e) => showTooltip("Strategic Overbooking", data.bookingStrategy.strategicOverbooking, e)}
            />
            
            {/* Safety Margin (Top) */}
            <div
              className="absolute w-full bg-data-neutral-grey border-t border-gray-300"
              style={{ 
                bottom: getPixelHeight(data.bookingStrategy.projectedAttendance + data.bookingStrategy.strategicOverbooking),
                height: getPixelHeight(data.bookingStrategy.safetyMargin),
                zIndex: 3,
              }}
              onMouseEnter={(e) => showTooltip("Safety Margin", data.bookingStrategy.safetyMargin, e)}
              onMouseLeave={hideTooltip}
              onMouseMove={(e) => showTooltip("Safety Margin", data.bookingStrategy.safetyMargin, e)}
            />
          </div>
          
          <h3 className="text-card-title text-nhs-black text-center">
            Booking Strategy
          </h3>
        </div>

        {/* Bar 2: Actual Outcome */}
        <div className="flex flex-col items-center gap-4">
          <div className="relative bg-nhs-light-grey rounded border border-nhs-mid-grey overflow-visible" 
               style={{ width: 80, height: maxHeight }}>
            
            {/* Actual Attendance (Bottom) */}
            <div
              className={`absolute bottom-0 w-full ${isOverCapacity ? 'bg-system-red' : 'bg-data-success-green'}`}
              style={{ 
                height: getPixelHeight(data.actualOutcome.actualAttendance),
                zIndex: 1,
              }}
              onMouseEnter={(e) => showTooltip("Actual Attendance", data.actualOutcome.actualAttendance, e)}
              onMouseLeave={hideTooltip}
              onMouseMove={(e) => showTooltip("Actual Attendance", data.actualOutcome.actualAttendance, e)}
            />
            
            {/* Wasted Capacity (Top) */}
            <div
              className="absolute w-full bg-data-neutral-grey border-t border-gray-300"
              style={{ 
                bottom: getPixelHeight(data.actualOutcome.actualAttendance),
                height: getPixelHeight(data.actualOutcome.wastedCapacity),
                zIndex: 2,
              }}
              onMouseEnter={(e) => showTooltip("Wasted Capacity", data.actualOutcome.wastedCapacity, e)}
              onMouseLeave={hideTooltip}
              onMouseMove={(e) => showTooltip("Wasted Capacity", data.actualOutcome.wastedCapacity, e)}
            />
          </div>
          
          <h3 className="text-card-title text-nhs-black text-center">
            Actual Outcome
          </h3>
        </div>
      </div>

      {/* Tooltip */}
      <AnimatePresence>
        {tooltip && (
          <motion.div
            className="fixed z-50 bg-nhs-black text-white px-3 py-2 rounded shadow-lg pointer-events-none"
            style={{ 
              left: tooltip.x + 10, 
              top: tooltip.y - 10,
            }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.15 }}
          >
            <div className="text-body-small font-medium">{tooltip.label}</div>
            <div className="text-body-small">{tooltip.value} guests</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
