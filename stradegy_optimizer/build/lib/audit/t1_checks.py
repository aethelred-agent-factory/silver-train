import logging
from data_bus.schemas import OptimizerProposal, TieredFinding

class T1Checks:
    """
    Tier 1 checks for structural integrity and critical failures.
    """
    def __init__(self, config):
        self.config = config
        self.audit_rules = config['audit_rules']['T1']
        self.parameter_bounds = config['parameter_bounds']
        logging.info("Initialized T1Checks.")

    def check_contradiction(self, proposal: OptimizerProposal) -> TieredFinding:
        """
        Checks for contradictions between regime and indicators.
        Example: Regime is RANGE but ATR percentile is very high.
        """
        context = proposal.context
        metrics = context.get('metrics_snapshot', {})
        
        # This check requires the metrics snapshot to contain relevant indicator values
        if (context.get('regime_label') == 'RANGE' and 
            metrics.get('atr_percentile_90', 0) > self.config['regime_config']['atr_percentile_thresholds']['high_volatility']):
            
            rule = next((r for r in self.audit_rules if r['name'] == 'T1_Contradiction'), None)
            if rule:
                return TieredFinding(
                    tier="T1",
                    code=rule['name'],
                    explanation=rule['description']
                )
        return None

    def check_bounds(self, proposal: OptimizerProposal) -> TieredFinding:
        """
        Checks if proposed parameters are within the defined safety bounds.
        """
        for param, value in proposal.proposed_parameters.items():
            if param in self.parameter_bounds:
                bounds = self.parameter_bounds[param]
                if not (bounds['min'] <= value <= bounds['max']):
                    rule = next((r for r in self.audit_rules if r['name'] == 'T1_BoundsViolation'), None)
                    if rule:
                        return TieredFinding(
                            tier="T1",
                            code=rule['name'],
                            explanation=f"Parameter '{param}' with value {value} is outside bounds [{bounds['min']}, {bounds['max']}]."
                        )
        return None
        
    def check_data_integrity(self, proposal: OptimizerProposal) -> TieredFinding:
        """
        Checks for significant data gaps based on context provided in proposal.
        """
        data_gap_pct = proposal.context.get('metrics_snapshot', {}).get('missing_data_pct', 0)
        gap_threshold = self.config['system_config']['thresholds'].get('t1_data_gap_threshold', 0.1)

        if data_gap_pct > gap_threshold:
            rule = next((r for r in self.audit_rules if r['name'] == 'T1_DataGap'), None)
            if rule:
                return TieredFinding(
                    tier="T1",
                    code=rule['name'],
                    explanation=f"Missing data ({data_gap_pct:.2%}) exceeds threshold ({gap_threshold:.2%})."
                )
        return None


    def run_all(self, proposal: OptimizerProposal) -> list[TieredFinding]:
        """
        Runs all T1 checks on a proposal.
        """
        logging.info(f"Running T1 checks for proposal {proposal.proposal_id}")
        findings = []
        
        # List of check functions to run
        check_functions = [
            self.check_contradiction,
            self.check_bounds,
            self.check_data_integrity
            # The arbitrary circularity check has been removed as per the audit.
            # Real circularity should be handled by the CausalChainValidator.
        ]
        
        for check_func in check_functions:
            finding = check_func(proposal)
            if finding:
                findings.append(finding)
                
        return findings