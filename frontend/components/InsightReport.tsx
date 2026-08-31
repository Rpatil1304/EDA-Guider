'use client';

export default function InsightReport() {
  const insights = [
    'Key insight 1',
    'Key insight 2',
    'Key insight 3',
  ];

  return (
    <div className="bg-blue-50 rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Key Insights</h2>
      <ul className="space-y-3">
        {insights.map((insight, index) => (
          <li key={index} className="flex items-start">
            <span className="text-blue-600 mr-3">•</span>
            <span>{insight}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
