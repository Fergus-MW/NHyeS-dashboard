"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DateNavigatorProps {
  selectedDate: Date;
  onDateSelect: (date: Date) => void;
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function DateNavigator({ selectedDate, onDateSelect }: DateNavigatorProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  
  // Get first day of month and number of days
  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);
  const firstDayWeekday = firstDayOfMonth.getDay();
  const daysInMonth = lastDayOfMonth.getDate();
  
  // Generate calendar days
  const calendarDays = [];
  
  // Add empty cells for days before first day of month
  for (let i = 0; i < firstDayWeekday; i++) {
    calendarDays.push(null);
  }
  
  // Add days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push(new Date(year, month, day));
  }
  
  // Check if date is available (not in the future, has data)
  const isDateAvailable = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    date.setHours(0, 0, 0, 0);
    return date <= today;
  };
  
  // Check if date is selected
  const isDateSelected = (date: Date) => {
    return (
      date.getDate() === selectedDate.getDate() &&
      date.getMonth() === selectedDate.getMonth() &&
      date.getFullYear() === selectedDate.getFullYear()
    );
  };
  
  const goToPreviousMonth = () => {
    setCurrentDate(new Date(year, month - 1));
  };
  
  const goToNextMonth = () => {
    const nextMonth = new Date(year, month + 1);
    const today = new Date();
    if (nextMonth <= today) {
      setCurrentDate(nextMonth);
    }
  };
  
  const handleDateClick = (date: Date) => {
    if (isDateAvailable(date)) {
      onDateSelect(date);
    }
  };

  return (
    <div className="p-2 h-full flex flex-col overflow-hidden scrollbar-hide">
      {/* Month Navigation */}
      <div className="flex items-center justify-between mb-2 flex-shrink-0">
        <Button
          variant="ghost"
          size="icon"
          onClick={goToPreviousMonth}
          className="text-nhs-blue hover:bg-nhs-grey-5 h-6 w-6"
        >
          <ChevronLeft className="h-3 w-3" />
        </Button>

        <h3 className="text-sm font-medium text-nhs-text-colour">
          {MONTHS[month].substring(0, 3)} {year}
        </h3>

        <Button
          variant="ghost"
          size="icon"
          onClick={goToNextMonth}
          disabled={new Date(year, month + 1) > new Date()}
          className="text-nhs-blue hover:bg-nhs-grey-5 disabled:opacity-50 h-6 w-6"
        >
          <ChevronRight className="h-3 w-3" />
        </Button>
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-0.5 flex-1 min-h-0">
        {/* Day Headers */}
        {DAYS.map((day) => (
          <div key={day} className="py-0.5 text-center text-[10px] font-medium text-nhs-secondary-text-colour flex items-center justify-center">
            {day.substring(0, 1)}
          </div>
        ))}

        {/* Calendar Days */}
        {calendarDays.map((date, index) => (
          <div key={index} className="flex items-center justify-center p-0">
            {date ? (
              <button
                onClick={() => handleDateClick(date)}
                disabled={!isDateAvailable(date)}
                className={cn(
                  "w-7 h-7 rounded-md text-xs font-medium transition-all duration-200",
                  "flex items-center justify-center",
                  "hover:bg-nhs-grey-5 focus:outline-none focus:ring-1 focus:ring-nhs-blue focus:ring-offset-1",
                  {
                    // Default state
                    "text-nhs-text-colour hover:text-nhs-blue": isDateAvailable(date) && !isDateSelected(date),

                    // Selected state
                    "bg-nhs-blue text-white hover:bg-nhs-dark-blue": isDateSelected(date),

                    // Disabled/unavailable state
                    "text-nhs-grey-3 cursor-not-allowed opacity-50": !isDateAvailable(date),
                  }
                )}
                aria-label={`Select ${date.toLocaleDateString()}`}
              >
                {date.getDate()}
              </button>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
