import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Settings, ZoomIn, ZoomOut, Eye } from "lucide-react";
import { Slider } from "@/components/ui/slider";

export function AccessibilityMenu() {
  const [textSize, setTextSize] = useState(100);
  const [highContrast, setHighContrast] = useState(false);

  const updateTextSize = (value: number[]) => {
    const newSize = value[0];
    setTextSize(newSize);
    document.documentElement.style.fontSize = `${newSize}%`;
  };

  const toggleHighContrast = () => {
    setHighContrast(!highContrast);
    document.documentElement.classList.toggle('high-contrast');
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Accessibility options">
          <Settings className="h-5 w-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56">
        <DropdownMenuLabel>Accessibility Settings</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <div className="px-2 py-1.5">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium">Text Size</span>
            <div className="flex items-center gap-2">
              <ZoomOut className="h-4 w-4" />
              <Slider
                value={[textSize]}
                onValueChange={updateTextSize}
                min={75}
                max={150}
                step={5}
                className="w-24"
              />
              <ZoomIn className="h-4 w-4" />
            </div>
          </div>
        </div>
        <DropdownMenuItem
          onSelect={toggleHighContrast}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            <span>High Contrast</span>
          </div>
          <div
            className={`h-4 w-4 rounded-full border ${
              highContrast ? 'bg-primary' : 'bg-secondary'
            }`}
          />
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
