import { Property } from '../types/chat';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Euro, MapPin, Bath, BedDouble, SquareIcon } from 'lucide-react';

interface PropertyCardProps {
  property: Property;
}

export function PropertyCard({ property }: PropertyCardProps) {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <Card className="overflow-hidden">
      <div className="aspect-video relative overflow-hidden">
        <img
          src={property.image_url || 'https://placehold.co/600x400?text=Property+Image'}
          alt={property.title}
          className="object-cover w-full h-full"
        />
        <Badge className="absolute top-2 right-2">{property.type}</Badge>
      </div>
      <CardHeader className="p-4">
        <CardTitle className="text-lg">{property.title}</CardTitle>
        <CardDescription className="flex items-center gap-1">
          <MapPin className="h-4 w-4" />
          {property.location}
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4 pt-0">
        <div className="flex justify-between mb-4">
          <div className="flex items-center gap-1">
            <BedDouble className="h-4 w-4" />
            <span className="text-sm">{property.bedrooms} beds</span>
          </div>
          <div className="flex items-center gap-1">
            <Bath className="h-4 w-4" />
            <span className="text-sm">{property.bathrooms} baths</span>
          </div>
          <div className="flex items-center gap-1">
            <SquareIcon className="h-4 w-4" />
            <span className="text-sm">{property.area} m²</span>
          </div>
        </div>
        <p className="text-sm line-clamp-2">{property.description}</p>
      </CardContent>
      <CardFooter className="p-4 pt-0 flex justify-between items-center">
        <div className="flex items-center gap-1">
          <Euro className="h-4 w-4" />
          <span className="font-bold">{formatPrice(property.price)}</span>
        </div>
        <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-primary-foreground">
          View Details
        </Badge>
      </CardFooter>
    </Card>
  );
}
