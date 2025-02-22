import logging
from pprint import pprint

from paasify_v4.common import to_yaml
import paasify_v4.exception as exc

logger = logging.getLogger(__name__)


class PaasifyEntityMixin:
    "Paasify entity mixin"

    def get_closest_parent(self):
        "Get closest parent"
        # Excepted for pods that returns closest stack
        return self

    def get_vars(self):
        "Get vars"
        raise NotImplementedError(f"Vars are not implemented for {self}")


class PodManagementMixin(PaasifyEntityMixin):
    "Pod management mixin"

    # Fname management

    def fparts(self, join=None, rev=False):
        "Return full name parts"
        final2 = []
        for parent in self.iter_parents(include_self=True):
            # print("PARENT", parent)
            # print("PARENT.parent", parent.parent)
            # print("PARENT.name", parent.name)
            # print()
            part_parent = parent.name or "MISSING"
            final2.append(part_parent)

        if not rev:
            final2.reverse()

        if not isinstance(join, str):
            return final2

        return join.join(final2)

    @property
    def fname(self):
        "Return full name"
        return self.fparts(join="_")

    @property
    def fname2(self):
        "Return full name"

        part_ns = self.ns.ident or "MISSING"
        part_stack = self.stack.ident or "MISSING"
        part_pod = self.ident or "MISSING"
        final2 = "__".join([part_ns, part_stack, part_pod])

        return final2

    # Pod management

    # IS IT A DUPLICATE OF ?
    def get_infos(self):
        "Get infos"

        out = {
            "kind": self.kind,
            "name": self.name,
            "path": +self.path,
            # "config": self.config,
            "vars": to_yaml(self.get_vars()),
        }
        # for var_name, var_value in self.config.items():
        #     out[f"config:{var_name}"] = var_value

        # for var_name, var_value in self.get_vars().items():
        #     # help(var_value.__class__)
        #     out[f"var:{var_name}"] = var_value #.get_values()
        return out

    def get_pods(self):
        "Return all pods in a list"
        raise NotImplementedError(f"Pod list is not implemented for {self}")

    def select_pods(self, selector=None):
        "Select a list of pods"

        all_pods = list(self.get_pods())
        pod_list = all_pods
        if selector:
            assert isinstance(
                selector, list
            ), f"Selector must be a list or None, got: {selector}"
            pod_list = []
            for pod in all_pods:
                if pod.name in selector:
                    pod_list.append(pod)

            # Return errors on unmatched items
            if len(pod_list) < len(selector):
                matches = [x.name for x in pod_list]
                unmatches = [x for x in selector if x not in matches]
                # pprint(pod_list)
                # print("UNMATCHES", unmatches)
                # print("MATCHES  ", matches)
                hints = ", ".join([x.name for x in all_pods])
                raise exc.PaasifyPodNotFoundError(
                    f"Pod not found: '{', '.join(unmatches)}', try instead: {hints}",
                    unmatches=unmatches,
                    hints=hints,
                )

        return pod_list

    def pod_build(self, selector=None):
        "Build pod"

        pod_list = self.select_pods(selector=selector)
        for pod in pod_list:
            pod.pod_build()

    def pod_up(self, selector=None):
        "Up pod"
        pod_list = self.select_pods(selector=selector)
        for pod in pod_list:
            pod.pod_up()

    def pod_down(self, selector=None):
        "Down pod"
        pod_list = self.select_pods(selector=selector)
        for pod in pod_list:
            pod.pod_down()


class PodManagedMixin(PodManagementMixin):
    "Pod managed mixin"

    def get_closest_parent(self):
        "Get closest parent"
        # Excepted for pods that returns closest stack, otheres returns self
        return self.stack

    def get_pods(self):
        "List pods"
        return [self]

    def pod_build(self, selector=None):
        "Build pod"

        raise NotImplementedError(f"Pod build is not implemented for {self}")
