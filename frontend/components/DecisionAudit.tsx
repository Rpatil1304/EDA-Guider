'use client';

interface Decision {
  column: string;
  action: string;
  reasoning: string;
}

export default function DecisionAudit({ decisions }: { decisions: Decision[] }) {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Decision Audit Trail</h2>
      {decisions.map((decision, index) => (
        <div key={index} className="border rounded-lg p-4 bg-gray-50">
          <h3 className="font-semibold">{decision.column}</h3>
          <p className="text-sm text-gray-600">Action: {decision.action}</p>
          <p className="text-sm">Reasoning: {decision.reasoning}</p>
        </div>
      ))}
    </div>
  );
}
