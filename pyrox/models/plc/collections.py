"""Collections of PLC objects.
"""
from collections import defaultdict
from typing import List, Optional, TYPE_CHECKING, Union
from pyrox.models.abc.list import HashList
from pyrox.models.plc import meta as plc_meta
from pyrox.models.plc.instruction import LogixInstruction
from pyrox.models.plc.routine import Routine

if TYPE_CHECKING:
    from .controller import Controller
    from .tag import Tag


class ContainsTags(plc_meta.NamedPlcObject):
    def __init__(
        self,
        meta_data: Optional[dict] = defaultdict(None),
        controller=None
    ) -> None:
        super().__init__(
            meta_data=meta_data,
            controller=controller
        )
        self._tags = None

    @property
    def raw_tags(self) -> list[dict]:
        if not self['Tags']:
            self['Tags'] = {'Tag': []}
        if not isinstance(self['Tags']['Tag'], list):
            self['Tags']['Tag'] = [self['Tags']['Tag']]
        return self['Tags']['Tag']

    @property
    def tags(self) -> HashList['Tag']:
        if self._tags is None:
            self._compile_tags()
        if self._tags is None:
            raise RuntimeError("tags could not be compiled")
        return self._tags

    @tags.setter
    def tags(self, value: Optional[HashList['Tag']]) -> None:
        if not isinstance(value, HashList) and value is not None:
            raise TypeError("tags must be a HashList")
        if value is None:
            value = HashList['Tag']('name')
        for tag in value:
            self._type_check(tag)
        self._redefine_raw_asset_list_from_asset_list(
            value,
            self.raw_tags
        )

    def _compile_from_meta_data(self):
        """compile this object from its meta data
        """
        self._compile_tags()

    def _compile_tags(self):
        """compile the tags in this container
        """
        if self._tags is None:
            self._tags = HashList('name')
        self._tags.clear()
        for tag in self.raw_tags:
            self.tags.append(
                self.config.tag_type(
                    meta_data=tag, controller=self.controller
                )
            )

    def _invalidate(self):
        self._tags = None

    def _type_check(
        self,
        tag: 'Tag'
    ) -> None:
        """Helper method to type check a tag

        Args:
            tag (Union[Tag, str]): tag to type check

        Raises:
            TypeError: if the tag is not a Tag object
        """
        from pyrox.models.plc import Tag  # avoid circular import
        if not isinstance(tag, Tag):
            raise TypeError("tag must be a Tag object")

    def add_tag(
        self,
        tag: 'Tag',
        index: Optional[int] = None,
        _inhibit_invalidate: bool = False
    ) -> None:
        """add a tag to this container

        Args:
            routine (Tag): tag to add
        """
        self._type_check(tag)
        self._add_asset_to_meta_data(
            tag,
            self.tags,
            self.raw_tags,
            index,
            _inhibit_invalidate
        )

    def add_tags(
        self,
        tags: List['Tag']
    ) -> None:
        """add multiple tags to this container

        Args:
            tags (List[Tag]): tags to add
        """
        for tag in tags:
            self.add_tag(tag, True)
        self._invalidate()

    def remove_tag(
        self,
        tag: 'Tag',
        _inhibit_invalidate: bool = False
    ) -> None:
        """remove a tag from this container

        Args:
            tag (Union[Tag, str]): tag to remove
            _inhibit_invalidate (bool): inhibit invalidation of the tag list. This is used when removing multiple tags at once.
        """
        self._type_check(tag)
        self._remove_asset_from_meta_data(
            tag,
            self.tags,
            self.raw_tags,
            _inhibit_invalidate
        )

    def remove_tags(
        self,
        tags: List['Tag']
    ) -> None:
        """remove multiple tags from this container

        Args:
            tags (List[Union[Tag, str]]): tags to remove
        """
        for tag in tags:
            self.remove_tag(tag, True)
        self._invalidate()


class ContainsRoutines(ContainsTags):
    """This PLC Object contains routines
    """

    def __init__(
        self,
        meta_data: Optional[dict] = defaultdict(None),
        controller: Optional['Controller'] = None
    ) -> None:
        super().__init__(
            meta_data,
            controller
        )

        self._input_instructions = None
        self._output_instructions = None
        self._instructions = None
        self._routines = None

    @property
    def class_(self) -> str:
        return self['@Class']

    @property
    def input_instructions(self) -> list[LogixInstruction]:
        if not self._input_instructions:
            self._compile_instructions()
        if self._input_instructions is None:
            raise RuntimeError("input_instructions could not be compiled")
        return self._input_instructions

    @property
    def instructions(self) -> list[LogixInstruction]:
        """get the instructions in this container

        Returns:
            :class:`list[LogixInstruction]`
        """
        if not self._instructions:
            self._compile_instructions()
        if self._instructions is None:
            raise RuntimeError("instructions could not be compiled")
        return self._instructions

    @property
    def output_instructions(self) -> list[LogixInstruction]:
        if not self._output_instructions:
            self._compile_instructions()
        if self._output_instructions is None:
            raise RuntimeError("output_instructions could not be compiled")
        return self._output_instructions

    @property
    def routines(self) -> HashList[Routine]:
        if not self._routines:
            self._compile_routines()
        if self._routines is None:
            raise RuntimeError("routines could not be compiled")
        return self._routines

    @routines.setter
    def routines(self, value: HashList[Routine]) -> None:
        if not isinstance(value, HashList):
            raise TypeError("routines must be a HashList")
        for routine in value:
            self._type_check(routine)
        self._redefine_raw_asset_list_from_asset_list(
            value,
            self.raw_routines
        )

    @property
    def raw_routines(self) -> list[dict]:
        if not self['Routines']:
            self['Routines'] = {'Routine': []}
        if not isinstance(self['Routines']['Routine'], list):
            self['Routines']['Routine'] = [self['Routines']['Routine']]
        return self['Routines']['Routine']

    def _compile_from_meta_data(self):
        """compile this object from its meta data
        """
        super()._compile_from_meta_data()
        self._compile_routines()
        self._compile_instructions()

    def _compile_instructions(self):
        """compile the instructions in this container
        """
        self._input_instructions = []
        self._output_instructions = []
        self._instructions = []

        for routine in self.routines:
            self._input_instructions.extend(routine.input_instructions)
            self._output_instructions.extend(routine.output_instructions)
            self._instructions.extend(routine.instructions)

    def _compile_routines(self):
        """compile the routines in this container

        This method compiles the routines from the raw metadata and initializes the HashList.
        """
        self._routines = HashList('name')
        for routine in self.raw_routines:
            self._routines.append(
                self.config.routine_type(
                    meta_data=routine,
                    controller=self.controller,
                    program=self
                )
            )

    def _invalidate(self):
        """invalidate this object

        This method is called when the object needs to be recompiled or reset.
        """
        super()._invalidate()
        self._input_instructions = []
        self._output_instructions = []
        self._instructions = []
        self._routines = HashList('name')

    def _type_check(  # type: ignore[override]
        self,
        routine: 'Routine'
    ) -> None:
        """Helper method to type check a routine

        Args:
            routine Routine: routine to type check

        Raises:
            TypeError: if the routine is not a Routine object
        """
        if not isinstance(routine, Routine):
            raise TypeError("routine must be a Routine object")

    def add_routine(
        self,
        routine: Routine,
        index: Optional[int] = None,
        _inhibit_invalidate: bool = False
    ) -> None:
        """add a routine to this container

        Args:
            routine (Routine): routine to add
        """
        self._type_check(routine)
        self._add_asset_to_meta_data(
            routine,
            self.routines,
            self.raw_routines,
            index,
            _inhibit_invalidate
        )

    def add_routines(
        self,
        routines: List[Routine]
    ) -> None:
        """add multiple routines to this container

        Args:
            routines (List[Routine]): routines to add
        """
        for routine in routines:
            self.add_routine(routine, True)
        self._invalidate()

    def check_routine_has_jsr(
        self,
        r: Union[str, Routine],
    ) -> bool:
        """Check if a routine contains a JSR to a specific routine.

        Args:
            r (str): The name of the routine to check for.
        Returns:
            bool: True if the routine contains a JSR to the specified routine, False otherwise.
        """
        if isinstance(r, Routine):
            r = r.name

        for routine in self.routines:
            if routine.name == r:
                continue  # Routines that call themselves are not considered
            if routine.check_for_jsr(r):
                return True
        return False

    def remove_routine(
        self,
        routine: Routine
    ) -> None:
        """remove a routine from this container

        Args:
            routine (Routine): routine to remove
        """
        self._type_check(routine)
        self._remove_asset_from_meta_data(
            routine,
            self.routines,
            self.raw_routines
        )

    def remove_routines(
        self,
        routines: List[Routine]
    ) -> None:
        """remove multiple routines from this container

        Args:
            routines (List[Union[Routine, str]]): routines to remove
        """
        for routine in routines:
            self.remove_routine(routine)
        self._invalidate()
