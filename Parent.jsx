import React, { useState } from 'react';
import Child from './Child';

function Parent() {
  // ...existing code...
  const [data, setData] = useState("Olá, componente filho!");

  return (
    <div>
      <h1>Componente Pai</h1>
      {/* Fluxo unidirecional: passando dados apenas do pai para o filho */}
      <Child data={data} />
    </div>
  );
}

export default Parent;
