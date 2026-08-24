export default function DecorativeShapes() {
  return (
    <div className="pointer-events-none fixed inset-0 z-[-10] overflow-hidden">
      {/* Red Semicircle (Right edge) */}
      <div 
        className="absolute top-[10%] -right-16 h-48 w-48 rounded-full bg-marker-red shadow-hard-md"
        style={{ clipPath: 'polygon(0 0, 50% 0, 50% 100%, 0 100%)' }}
      ></div>

      {/* Yellow Pentagon (Top left) */}
      <div 
        className="absolute top-[15%] left-[5%] h-32 w-32 bg-hi-yellow shadow-hard-md clip-pentagon"
        style={{ transform: 'rotate(-15deg)' }}
      ></div>

      {/* Powder Sky Circle (Bottom left) */}
      <div 
        className="absolute bottom-[20%] left-[8%] h-40 w-40 rounded-full bg-powder-sky shadow-hard-sm"
      ></div>

      {/* Jelly Green Triangle (Middle right) */}
      <div 
        className="absolute top-[45%] right-[12%] h-24 w-24 bg-jelly-green shadow-hard-sm clip-triangle"
        style={{ transform: 'rotate(45deg)' }}
      ></div>
      
      {/* Bubblegum Pink Star (Bottom right) */}
      <div 
        className="absolute bottom-[10%] right-[20%] h-28 w-28 bg-bubblegum-pink shadow-hard-sm clip-star"
        style={{ transform: 'rotate(-10deg)' }}
      ></div>
    </div>
  );
}
