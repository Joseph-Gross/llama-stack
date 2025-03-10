import { useState } from 'react';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';
import { Filter } from 'lucide-react';

interface PropertyFiltersProps {
  onApplyFilters: (filters: {
    propertyType: string;
    location: string;
    priceRange: string;
  }) => void;
}

export function PropertyFilters({ onApplyFilters }: PropertyFiltersProps) {
  const [propertyType, setPropertyType] = useState('');
  const [location, setLocation] = useState('');
  const [priceRange, setPriceRange] = useState('');

  const handleApplyFilters = () => {
    onApplyFilters({
      propertyType,
      location,
      priceRange,
    });
  };

  return (
    <Accordion type="single" collapsible className="mb-4">
      <AccordionItem value="filters">
        <AccordionTrigger className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <span>Property Filters</span>
        </AccordionTrigger>
        <AccordionContent>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label htmlFor="property-type">Property Type</Label>
              <Select value={propertyType} onValueChange={setPropertyType}>
                <SelectTrigger id="property-type">
                  <SelectValue placeholder="Select property type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Any</SelectItem>
                  <SelectItem value="apartment">Apartment</SelectItem>
                  <SelectItem value="villa">Villa</SelectItem>
                  <SelectItem value="townhouse">Townhouse</SelectItem>
                  <SelectItem value="house">House</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="location">Location</Label>
              <Select value={location} onValueChange={setLocation}>
                <SelectTrigger id="location">
                  <SelectValue placeholder="Select location" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Any</SelectItem>
                  <SelectItem value="Madrid">Madrid</SelectItem>
                  <SelectItem value="Barcelona">Barcelona</SelectItem>
                  <SelectItem value="Valencia">Valencia</SelectItem>
                  <SelectItem value="Seville">Seville</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="price-range">Price Range</Label>
              <Select value={priceRange} onValueChange={setPriceRange}>
                <SelectTrigger id="price-range">
                  <SelectValue placeholder="Select price range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Any</SelectItem>
                  <SelectItem value="0-200000">Up to €200,000</SelectItem>
                  <SelectItem value="200000-500000">€200,000 - €500,000</SelectItem>
                  <SelectItem value="500000-1000000">€500,000 - €1,000,000</SelectItem>
                  <SelectItem value="1000000+">€1,000,000+</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleApplyFilters}>Apply Filters</Button>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
