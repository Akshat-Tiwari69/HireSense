import React from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { TabsContent } from '../../ui/tabs';
import { Shield, Edit } from 'lucide-react';

const SettingsTab = ({
  envStatus,
  editingEnvVar,
  envVarValue,
  setEnvVarValue,
  handleEditEnvVar,
  handleSaveEnvVar,
  handleCancelEdit,
}) => (
  <TabsContent value="settings">
    <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
      <CardHeader>
        <CardTitle className="text-slate-900">Environment Variables</CardTitle>
        <CardDescription className="text-slate-600">
          Configure environment variables. Changes are persisted to .env file and require backend restart to take effect.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {Object.entries(envStatus).map(([key, value]) => (
            <div key={key} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-slate-900 font-mono text-sm font-semibold">{key}</span>
                    {value ? (
                      <Badge className="bg-green-600">
                        <Shield className="w-3 h-3 mr-1" />
                        Configured
                      </Badge>
                    ) : (
                      <Badge className="bg-red-600">Not Set</Badge>
                    )}
                  </div>

                  {editingEnvVar === key ? (
                    <div className="space-y-2">
                      <Input
                        type="text"
                        placeholder={`Enter ${key} value`}
                        value={envVarValue}
                        onChange={(e) => setEnvVarValue(e.target.value)}
                        className="font-mono text-sm"
                      />
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={handleSaveEnvVar}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          Save
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleCancelEdit}
                          className="border-slate-300"
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      {value && (
                        <span className="text-xs text-slate-500 font-mono">{value}</span>
                      )}
                    </div>
                  )}
                </div>

                {editingEnvVar !== key && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEditEnvVar(key, value)}
                    className="border-indigo-300 text-indigo-700 hover:bg-indigo-50"
                  >
                    <Edit className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  </TabsContent>
);

export default SettingsTab;
