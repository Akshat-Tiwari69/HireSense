import React from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../../ui/dialog';
import { Label } from '../../ui/label';
import { Loader2, Sparkles } from 'lucide-react';
import { api } from '../../../services/api';
import { useToast } from '../../../hooks/use-toast';

const SectorModal = ({
  sectorModalOpen,
  setSectorModalOpen,
  sectorForm,
  setSectorForm,
  enhancingSector,
  setEnhancingSector,
  handleSaveSector,
}) => {
  const { toast } = useToast();

  return (
    <Dialog open={sectorModalOpen} onOpenChange={setSectorModalOpen}>
      <DialogContent className="bg-white border-slate-200 shadow-md">
        <DialogHeader>
          <DialogTitle className="text-slate-900">Create Sector</DialogTitle>
          <DialogDescription className="text-slate-600">Add a new organizational sector for job postings and access control</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label className="text-slate-700">Sector Name *</Label>
            <Input
              value={sectorForm.name}
              onChange={(e) => setSectorForm({ ...sectorForm, name: e.target.value })}
              className="bg-white border-slate-300 text-slate-900"
              placeholder="e.g., Product Engineering"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-slate-700">Description</Label>
            <Input
              value={sectorForm.description}
              onChange={(e) => setSectorForm({ ...sectorForm, description: e.target.value })}
              className="bg-white border-slate-300 text-slate-900"
              placeholder="Brief description of the sector"
            />
          </div>
          {/* AI Enhance Button */}
          {(sectorForm.name || sectorForm.description) && (
            <Button
              type="button"
              variant="outline"
              className="border-purple-300 text-purple-700 hover:bg-purple-50"
              disabled={enhancingSector}
              onClick={async () => {
                setEnhancingSector(true);
                try {
                  const res = await api.post('/api/admin/ai-enhance', {
                    type: 'sector',
                    title: sectorForm.name,
                    description: sectorForm.description
                  });
                  if (res.data.status === 'success') {
                    setSectorForm(prev => ({
                      ...prev,
                      name: res.data.enhanced_title || prev.name,
                      description: res.data.enhanced_description || prev.description
                    }));
                    toast({ title: 'Enhanced', description: 'Sector name and description polished by AI', duration: 3000 });
                  } else {
                    toast({ title: 'AI Error', description: res.data.message, variant: 'destructive' });
                  }
                } catch (err) {
                  toast({ title: 'AI Error', description: err.response?.data?.message || err.message, variant: 'destructive' });
                } finally {
                  setEnhancingSector(false);
                }
              }}
            >
              {enhancingSector ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}
              {enhancingSector ? 'Enhancing...' : 'Enhance with AI'}
            </Button>
          )}
          <div className="space-y-2">
            <Label className="text-slate-700">Email Alias</Label>
            <Input
              value={sectorForm.email_alias}
              onChange={(e) => setSectorForm({ ...sectorForm, email_alias: e.target.value })}
              className="bg-white border-slate-300 text-slate-900"
              placeholder="e.g., eng@company.com"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setSectorModalOpen(false)} className="border-slate-300 text-slate-700">Cancel</Button>
          <Button onClick={handleSaveSector} className="bg-indigo-600 hover:bg-indigo-700">Create</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default SectorModal;
