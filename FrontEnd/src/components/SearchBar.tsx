import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  isLoading: boolean;
}

export function SearchBar({ value, onChange, onSearch, isLoading }: SearchBarProps) {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      onSearch();
    }
  };

  return (
    <div className="flex gap-3 w-full max-w-2xl mx-auto">
      <div className="relative flex-1">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search for recipes... try 'sushi with rice' or 'Italian pizza'"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          className="pl-12 pr-4 h-14 text-base rounded-full border-2 border-border bg-card shadow-card focus:shadow-card-hover focus:border-primary transition-all duration-300"
        />
      </div>
      <Button
        onClick={onSearch}
        disabled={isLoading}
        className="h-14 px-8 rounded-full font-semibold shadow-card hover:shadow-card-hover transition-all duration-300"
      >
        {isLoading ? (
          <div className="h-5 w-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
        ) : (
          "Search"
        )}
      </Button>
    </div>
  );
}
