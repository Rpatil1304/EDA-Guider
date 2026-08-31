'use client';

interface Column {
  name: string;
  type: string;
  missing: number;
  unique: number;
}

export default function ProfileTable({ columns }: { columns: Column[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-2">Column</th>
            <th className="border p-2">Type</th>
            <th className="border p-2">Missing</th>
            <th className="border p-2">Unique</th>
          </tr>
        </thead>
        <tbody>
          {columns.map((col) => (
            <tr key={col.name}>
              <td className="border p-2">{col.name}</td>
              <td className="border p-2">{col.type}</td>
              <td className="border p-2">{col.missing}</td>
              <td className="border p-2">{col.unique}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
